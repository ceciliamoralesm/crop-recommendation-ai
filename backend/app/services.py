"""Casos de uso: carga de datasets, re-entrenamiento y versionado de modelos."""
import logging
import threading
from pathlib import Path

import pandas as pd
from sqlalchemy import func, insert, select, update
from sqlalchemy.orm import Session

from . import ml
from .config import settings
from .models import Dataset, ModelVersion, TrainingSample

log = logging.getLogger("crop_ai")
_retrain_lock = threading.Lock()


class RetrainBusy(RuntimeError):
    pass


def active_model(db: Session) -> ModelVersion | None:
    return db.scalar(select(ModelVersion).where(ModelVersion.is_active))


def load_active_into_store(db: Session) -> bool:
    """Carga el modelo activo. Devuelve False si su archivo .joblib no existe."""
    mv = active_model(db)
    if not mv:
        return False
    if not Path(mv.model_path).exists():
        log.warning("No se encuentra el archivo del modelo v%s (%s)", mv.version, mv.model_path)
        return False
    ml.model_store.load(mv.model_path, mv.id, mv.version)
    log.info("Modelo activo cargado: v%s", mv.version)
    return True


def active_samples_df(db: Session) -> pd.DataFrame:
    rows = db.execute(
        select(TrainingSample.n, TrainingSample.p, TrainingSample.k, TrainingSample.temperature,
               TrainingSample.humidity, TrainingSample.ph, TrainingSample.rainfall, TrainingSample.label)
        .join(Dataset).where(Dataset.is_active)
    ).all()
    return pd.DataFrame(rows, columns=ml.FEATURES + [ml.TARGET])


def count_active_samples(db: Session) -> int:
    return db.scalar(select(func.count(TrainingSample.id)).join(Dataset).where(Dataset.is_active)) or 0


def ingest_dataset(db: Session, df: pd.DataFrame, filename: str, mode: str, notes: str | None = None) -> Dataset:
    if mode == "replace":
        db.execute(update(Dataset).values(is_active=False))
    ds = Dataset(filename=filename, n_rows=len(df), is_active=True, notes=notes)
    db.add(ds)
    db.flush()
    records = [
        {"dataset_id": ds.id, "n": r.N, "p": r.P, "k": r.K, "temperature": r.temperature,
         "humidity": r.humidity, "ph": r.ph, "rainfall": r.rainfall, "label": r.label}
        for r in df.itertuples(index=False)
    ]
    db.execute(insert(TrainingSample), records)
    db.commit()
    return ds


def retrain(db: Session, force: bool = False) -> dict:
    """Entrena con todos los datasets activos. Activa el nuevo modelo si no empeora (o si force=True)."""
    if not _retrain_lock.acquire(blocking=False):
        raise RetrainBusy("Ya hay un re-entrenamiento en curso.")
    try:
        df = active_samples_df(db)
        if df.empty:
            raise ml.DataValidationError("No hay datos de entrenamiento activos.")
        result = ml.train(df)

        next_version = (db.scalar(select(func.max(ModelVersion.version))) or 0) + 1
        path = settings.models_dir / f"model_v{next_version}.joblib"
        ml.save(result, path)

        m = result.metrics
        mv = ModelVersion(
            version=next_version, algorithm=m["algorithm"], n_train=m["n_train"], n_test=m["n_test"],
            accuracy=m["accuracy"], precision_macro=m["precision_macro"], recall_macro=m["recall_macro"],
            f1_macro=m["f1_macro"], cv_f1_mean=m["cv_f1_mean"], cv_f1_std=m["cv_f1_std"],
            classes=m["classes"], confusion_matrix=m["confusion_matrix"], per_class=m["per_class"],
            hyperparams=m["hyperparams"], model_path=str(path), is_active=False,
        )
        db.add(mv)

        current = active_model(db)
        prev_version = current.version if current else None
        prev_f1 = current.f1_macro if current else None
        if current is None:
            activate, reason = True, "No había un modelo activo."
        elif force:
            activate, reason = True, "Activación forzada (force=true)."
        elif m["f1_macro"] >= current.f1_macro - settings.retrain_tolerance:
            activate, reason = True, (
                f"F1 nuevo {m['f1_macro']:.4f} >= F1 actual {current.f1_macro:.4f} - tolerancia {settings.retrain_tolerance}."
            )
        else:
            activate, reason = False, (
                f"F1 nuevo {m['f1_macro']:.4f} empeora respecto al actual {current.f1_macro:.4f}; se mantiene v{current.version}."
            )

        if activate:
            db.execute(update(ModelVersion).where(ModelVersion.is_active).values(is_active=False))
            db.flush()
            mv.is_active = True
        db.commit()
        db.refresh(mv)
        if activate:
            ml.model_store.load(mv.model_path, mv.id, mv.version)

        return {"new_version": mv.version, "activated": activate, "reason": reason,
                "previous_version": prev_version, "previous_f1_macro": prev_f1, "metrics": mv}
    except Exception:
        db.rollback()
        raise
    finally:
        _retrain_lock.release()


def activate_version(db: Session, mv: ModelVersion) -> None:
    db.execute(update(ModelVersion).where(ModelVersion.is_active).values(is_active=False))
    db.flush()
    mv.is_active = True
    db.commit()
    ml.model_store.load(mv.model_path, mv.id, mv.version)


def bootstrap(db: Session) -> None:
    """Al arrancar: carga el CSV semilla si la BD está vacía y entrena el primer modelo si no hay ninguno."""
    if db.scalar(select(func.count(Dataset.id))) == 0 and settings.seed_csv.exists():
        df, report = ml.parse_and_validate_csv(settings.seed_csv.read_bytes())
        ingest_dataset(db, df, settings.seed_csv.name, "append", notes="Dataset semilla (Kaggle)")
        log.info("Dataset semilla cargado: %s", report)
    if not load_active_into_store(db) and count_active_samples(db) > 0:
        log.info("Entrenando modelo (no hay un modelo activo disponible)...")
        retrain(db, force=True)
