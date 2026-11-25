from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from .. import ml
from ..database import get_db
from ..models import Prediction
from ..schemas import PredictionItem, PredictionPage, PredictRequest, PredictResponse

router = APIRouter(prefix="/api", tags=["Predicciones"])


@router.post("/predict", response_model=PredictResponse, summary="Recomendar un cultivo",
             responses={503: {"description": "No hay modelo activo"}})
def predict(body: PredictRequest, db: Session = Depends(get_db)):
    """Envía las condiciones del suelo y el clima al modelo activo y devuelve el cultivo recomendado,
    su confianza y el top 3. La predicción se guarda en el historial."""
    if not ml.model_store.ready:
        raise HTTPException(503, "No hay un modelo activo. Sube un dataset y re-entrena.")
    features = body.model_dump()
    out = ml.model_store.predict(features)
    pred = Prediction(
        model_version_id=out["model_version_id"], n=body.N, p=body.P, k=body.K,
        temperature=body.temperature, humidity=body.humidity, ph=body.ph, rainfall=body.rainfall,
        predicted_label=out["label"], confidence=out["confidence"], top3=out["top3"],
    )
    db.add(pred)
    db.commit()
    db.refresh(pred)
    return PredictResponse(id=pred.id, label=out["label"], confidence=out["confidence"], top3=out["top3"],
                           warnings=out["warnings"], model_version=out["model_version"], created_at=pred.created_at)


def _to_item(p: Prediction) -> PredictionItem:
    return PredictionItem(
        id=p.id,
        input=PredictRequest(N=p.n, P=p.p, K=p.k, temperature=p.temperature, humidity=p.humidity, ph=p.ph,
                             rainfall=p.rainfall),
        predicted_label=p.predicted_label, confidence=p.confidence, top3=p.top3,
        model_version=p.model_version.version, created_at=p.created_at,
    )


@router.get("/predictions", response_model=PredictionPage, summary="Historial de predicciones")
def list_predictions(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    label: str | None = Query(None, description="Filtrar por cultivo predicho"),
    db: Session = Depends(get_db),
):
    """Devuelve las predicciones previas (datos enviados y resultado), de la más reciente a la más antigua."""
    q = select(Prediction)
    if label:
        q = q.where(Prediction.predicted_label == label.lower())
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    rows = db.scalars(
        q.options(joinedload(Prediction.model_version))
        .order_by(Prediction.created_at.desc(), Prediction.id.desc())
        .offset((page - 1) * size).limit(size)
    ).all()
    return PredictionPage(items=[_to_item(p) for p in rows], total=total, page=page, size=size)


@router.get("/predictions/{prediction_id}", response_model=PredictionItem, summary="Detalle de una predicción")
def get_prediction(prediction_id: int, db: Session = Depends(get_db)):
    p = db.get(Prediction, prediction_id)
    if not p:
        raise HTTPException(404, "Predicción no encontrada")
    return _to_item(p)
