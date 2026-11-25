import io
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import ml, services
from ..config import settings
from ..database import get_db
from ..models import Dataset, TrainingSample
from ..schemas import DatasetInfo, DatasetSummary, UploadResponse

router = APIRouter(prefix="/api/datasets", tags=["Datos de entrenamiento"])


@router.post("/upload", response_model=UploadResponse, summary="Subir archivo de entrenamiento (CSV)",
             responses={413: {"description": "Archivo demasiado grande"}, 422: {"description": "CSV inválido"}})
async def upload(
    file: UploadFile = File(..., description="CSV con columnas N,P,K,temperature,humidity,ph,rainfall,label"),
    mode: Literal["append", "replace"] = Form("append", description="append: se suma a los datos actuales; "
                                                                    "replace: sustituye a los datos activos"),
    retrain: bool = Form(False, description="Re-entrenar automáticamente tras la carga"),
    db: Session = Depends(get_db),
):
    """Valida el archivo (columnas, tipos, rangos y duplicados), lo guarda en la base de datos y,
    opcionalmente, re-entrena el modelo."""
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(422, "El archivo debe ser .csv")
    raw = await file.read()
    if len(raw) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"Máximo {settings.max_upload_mb} MB")
    try:
        df, report = ml.parse_and_validate_csv(raw)
    except ml.DataValidationError as e:
        raise HTTPException(422, str(e)) from e

    ds = services.ingest_dataset(db, df, file.filename, mode)
    retrain_out = None
    if retrain:
        try:
            retrain_out = services.retrain(db)
        except (ml.DataValidationError, services.RetrainBusy) as e:
            raise HTTPException(422, f"Datos guardados, pero el re-entrenamiento falló: {e}") from e
    return UploadResponse(dataset=ds, mode=mode, validation=report,
                          total_active_samples=services.count_active_samples(db), retrain=retrain_out)


@router.get("", response_model=DatasetSummary, summary="Datasets cargados y distribución de clases")
def summary(db: Session = Depends(get_db)):
    datasets = db.scalars(select(Dataset).order_by(Dataset.uploaded_at.desc())).all()
    dist = dict(db.execute(
        select(TrainingSample.label, func.count()).join(Dataset).where(Dataset.is_active)
        .group_by(TrainingSample.label).order_by(TrainingSample.label)
    ).all())
    return DatasetSummary(datasets=datasets, total_active_samples=sum(dist.values()), class_distribution=dist)


@router.patch("/{dataset_id}", response_model=DatasetInfo, summary="Activar/desactivar un dataset")
def toggle(dataset_id: int, is_active: bool, db: Session = Depends(get_db)):
    ds = db.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset no encontrado")
    ds.is_active = is_active
    db.commit()
    return ds


@router.get("/template", summary="Descargar plantilla CSV", response_class=StreamingResponse)
def template():
    content = ",".join(ml.FEATURES + [ml.TARGET]) + "\n90,42,43,20.88,82.0,6.5,202.9,rice\n"
    return StreamingResponse(io.BytesIO(content.encode()), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=plantilla_cultivos.csv"})
