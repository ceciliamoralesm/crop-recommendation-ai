import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from . import ml, services
from .config import settings
from .database import Base, SessionLocal, engine
from .routers import datasets, models, predictions
from .schemas import Health

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)  # idempotente; el esquema oficial está en db/schema.sql
    with SessionLocal() as db:
        services.bootstrap(db)
    yield


app = FastAPI(
    title="Crop Recommendation AI",
    version="1.0.0",
    description=(
        "Servicio de IA que recomienda el cultivo más adecuado según las condiciones del suelo "
        "(N, P, K, pH) y del clima (temperatura, humedad, lluvia).\n\n"
        "Modelo: RandomForest multiclase (22 cultivos), entrenado siguiendo CRISP-ML(Q)."
    ),
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Predicciones", "description": "Predecir y consultar el historial"},
        {"name": "Modelo", "description": "Métricas, re-entrenamiento y versiones"},
        {"name": "Datos de entrenamiento", "description": "Carga y gestión de datasets"},
        {"name": "Sistema", "description": "Estado del servicio"},
    ],
)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"])
app.include_router(predictions.router)
app.include_router(models.router)
app.include_router(datasets.router)


@app.get("/api/health", response_model=Health, tags=["Sistema"], summary="Estado del servicio")
def health():
    try:
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
        db_ok = True
    except Exception:  # noqa: BLE001
        db_ok = False
    return Health(status="ok" if db_ok and ml.model_store.ready else "degraded", database=db_ok,
                  model_loaded=ml.model_store.ready, active_model_version=ml.model_store.version)
