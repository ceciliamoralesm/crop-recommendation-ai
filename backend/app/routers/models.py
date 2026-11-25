from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import ml, services
from ..database import get_db
from ..models import ModelVersion
from ..schemas import ModelMetrics, ModelSummary, RetrainResponse

router = APIRouter(prefix="/api", tags=["Modelo"])


@router.get("/metrics", response_model=ModelMetrics, summary="Métricas del modelo activo",
            responses={404: {"description": "No hay modelo activo"}})
def metrics(version: int | None = Query(None, description="Versión concreta; si se omite, la activa"),
            db: Session = Depends(get_db)):
    """Accuracy, precision, recall y F1 (macro), F1 de validación cruzada, matriz de confusión,
    métricas por clase e importancia de variables."""
    if version is None:
        mv = services.active_model(db)
    else:
        mv = db.scalar(select(ModelVersion).where(ModelVersion.version == version))
    if not mv:
        raise HTTPException(404, "Modelo no encontrado")
    return mv


@router.post("/retrain", response_model=RetrainResponse, summary="Re-entrenar el modelo",
             responses={409: {"description": "Re-entrenamiento en curso"}, 422: {"description": "Datos insuficientes"}})
def retrain(force: bool = Query(False, description="Activar el nuevo modelo aunque tenga peor F1"),
            db: Session = Depends(get_db)):
    """Entrena una nueva versión con todos los datasets activos de la base de datos. El nuevo modelo
    se activa si su F1 macro no empeora más que la tolerancia configurada (o si `force=true`)."""
    try:
        return services.retrain(db, force=force)
    except services.RetrainBusy as e:
        raise HTTPException(409, str(e)) from e
    except ml.DataValidationError as e:
        raise HTTPException(422, str(e)) from e


@router.get("/models", response_model=list[ModelSummary], summary="Versiones del modelo")
def list_models(db: Session = Depends(get_db)):
    return db.scalars(select(ModelVersion).order_by(ModelVersion.version.desc())).all()


@router.post("/models/{version}/activate", response_model=ModelSummary, summary="Activar una versión (rollback)")
def activate(version: int, db: Session = Depends(get_db)):
    mv = db.scalar(select(ModelVersion).where(ModelVersion.version == version))
    if not mv:
        raise HTTPException(404, "Modelo no encontrado")
    services.activate_version(db, mv)
    return mv
