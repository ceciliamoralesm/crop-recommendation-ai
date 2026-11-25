"""Entrenamiento, evaluación y carga del modelo (lógica de ML independiente de la API)."""
import io
import threading
from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
TARGET = "label"
# Hiperparámetros elegidos con GridSearchCV en notebooks/01_eda_y_entrenamiento.ipynb
HYPERPARAMS = {"n_estimators": 200, "max_depth": None, "min_samples_split": 5, "random_state": 42}

# Rangos físicamente válidos (validación de calidad de datos al cargar CSV)
VALID_RANGES = {
    "N": (0, 300), "P": (0, 300), "K": (0, 300),
    "temperature": (-10, 60), "humidity": (0, 100), "ph": (0, 14), "rainfall": (0, 1000),
}
MIN_SAMPLES_PER_CLASS = 5


class DataValidationError(ValueError):
    pass


@dataclass
class TrainResult:
    pipeline: Pipeline
    metrics: dict
    feature_ranges: dict = field(default_factory=dict)


def parse_and_validate_csv(raw: bytes) -> tuple[pd.DataFrame, dict]:
    """Lee un CSV, valida esquema y rangos. Devuelve (df_limpio, reporte)."""
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as e:  # noqa: BLE001
        raise DataValidationError(f"No se pudo leer el CSV: {e}") from e

    df.columns = [c.strip() for c in df.columns]
    missing = [c for c in FEATURES + [TARGET] if c not in df.columns]
    if missing:
        raise DataValidationError(f"Faltan columnas obligatorias: {missing}. Se esperan: {FEATURES + [TARGET]}")

    df = df[FEATURES + [TARGET]].copy()
    total = len(df)
    for c in FEATURES:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df[TARGET] = df[TARGET].astype(str).str.strip().str.lower()
    df.loc[df[TARGET].isin(["", "nan", "none"]), TARGET] = np.nan

    null_mask = df.isna().any(axis=1)
    range_mask = pd.Series(False, index=df.index)
    for c, (lo, hi) in VALID_RANGES.items():
        range_mask |= (df[c] < lo) | (df[c] > hi)
    bad = null_mask | range_mask
    clean = df[~bad]
    dup = int(clean.duplicated().sum())
    clean = clean.drop_duplicates().reset_index(drop=True)

    if clean.empty:
        raise DataValidationError("El archivo no contiene filas válidas.")

    report = {
        "total_rows": total,
        "valid_rows": len(clean),
        "rejected_null_or_non_numeric": int(null_mask.sum()),
        "rejected_out_of_range": int((range_mask & ~null_mask).sum()),
        "duplicates_removed": dup,
        "classes": int(clean[TARGET].nunique()),
    }
    return clean, report


def train(df: pd.DataFrame) -> TrainResult:
    """Entrena el pipeline (StandardScaler + RandomForest) y calcula métricas en test 80/20 estratificado."""
    counts = df[TARGET].value_counts()
    small = counts[counts < MIN_SAMPLES_PER_CLASS]
    if len(small):
        raise DataValidationError(
            f"Clases con menos de {MIN_SAMPLES_PER_CLASS} muestras (no se puede estratificar): {small.to_dict()}"
        )
    if df[TARGET].nunique() < 2:
        raise DataValidationError("Se necesitan al menos 2 clases para entrenar.")

    X, y = df[FEATURES], df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    def make() -> Pipeline:
        return Pipeline([("scaler", StandardScaler()), ("clf", RandomForestClassifier(**HYPERPARAMS))])

    n_splits = int(min(5, y_train.value_counts().min()))
    cv_scores = cross_val_score(
        make(), X_train, y_train, scoring="f1_macro",
        cv=StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42),
    )

    pipe = make().fit(X_train, y_train)
    y_pred = pipe.predict(X_test)
    classes = list(pipe.classes_)
    p, r, f, s = precision_recall_fscore_support(y_test, y_pred, labels=classes, zero_division=0)
    pm, rm, fm, _ = precision_recall_fscore_support(y_test, y_pred, average="macro", zero_division=0)

    metrics = {
        "algorithm": "RandomForestClassifier (StandardScaler pipeline)",
        "n_train": len(X_train),
        "n_test": len(X_test),
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision_macro": float(pm),
        "recall_macro": float(rm),
        "f1_macro": float(fm),
        "cv_f1_mean": float(cv_scores.mean()),
        "cv_f1_std": float(cv_scores.std()),
        "classes": classes,
        "confusion_matrix": confusion_matrix(y_test, y_pred, labels=classes).tolist(),
        "per_class": {
            c: {"precision": float(p[i]), "recall": float(r[i]), "f1": float(f[i]), "support": int(s[i])}
            for i, c in enumerate(classes)
        },
        "hyperparams": {
            **{k: v for k, v in HYPERPARAMS.items()},
            "feature_importances": dict(zip(FEATURES, map(float, pipe.named_steps["clf"].feature_importances_))),
        },
    }
    ranges = {c: (float(df[c].min()), float(df[c].max())) for c in FEATURES}
    return TrainResult(pipeline=pipe, metrics=metrics, feature_ranges=ranges)


def save(result: TrainResult, path: Path) -> None:
    joblib.dump({"pipeline": result.pipeline, "feature_ranges": result.feature_ranges}, path)


class ModelStore:
    """Mantiene en memoria el modelo activo (thread-safe)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pipeline: Pipeline | None = None
        self._ranges: dict = {}
        self.version_id: int | None = None
        self.version: int | None = None

    def load(self, path: str, version_id: int, version: int) -> None:
        bundle = joblib.load(path)
        with self._lock:
            self._pipeline = bundle["pipeline"]
            self._ranges = bundle.get("feature_ranges", {})
            self.version_id, self.version = version_id, version

    @property
    def ready(self) -> bool:
        return self._pipeline is not None

    def predict(self, features: dict[str, float]) -> dict:
        with self._lock:
            if self._pipeline is None:
                raise RuntimeError("No hay un modelo activo cargado.")
            pipe, ranges, vid, ver = self._pipeline, self._ranges, self.version_id, self.version
        X = pd.DataFrame([[features[c] for c in FEATURES]], columns=FEATURES)
        proba = pipe.predict_proba(X)[0]
        order = np.argsort(proba)[::-1][:3]
        top3 = [{"label": str(pipe.classes_[i]), "probability": round(float(proba[i]), 4)} for i in order]
        warnings = [
            f"{c}={features[c]} está fuera del rango visto en entrenamiento [{lo:g}, {hi:g}]"
            for c, (lo, hi) in ranges.items()
            if not lo <= features[c] <= hi
        ]
        return {
            "label": top3[0]["label"], "confidence": top3[0]["probability"], "top3": top3,
            "warnings": warnings, "model_version_id": vid, "model_version": ver,
        }


model_store = ModelStore()
