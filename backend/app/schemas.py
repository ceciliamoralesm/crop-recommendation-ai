from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PredictRequest(BaseModel):
    """Condiciones de suelo y clima de la parcela."""
    model_config = ConfigDict(json_schema_extra={"example": {
        "N": 90, "P": 42, "K": 43, "temperature": 20.88, "humidity": 82.0, "ph": 6.5, "rainfall": 202.9}})

    N: float = Field(..., ge=0, le=300, description="Nitrógeno en el suelo (kg/ha)")
    P: float = Field(..., ge=0, le=300, description="Fósforo en el suelo (kg/ha)")
    K: float = Field(..., ge=0, le=300, description="Potasio en el suelo (kg/ha)")
    temperature: float = Field(..., ge=-10, le=60, description="Temperatura media (°C)")
    humidity: float = Field(..., ge=0, le=100, description="Humedad relativa (%)")
    ph: float = Field(..., ge=0, le=14, description="pH del suelo")
    rainfall: float = Field(..., ge=0, le=1000, description="Precipitación (mm)")


class LabelProb(BaseModel):
    label: str
    probability: float


class PredictResponse(BaseModel):
    id: int = Field(description="ID de la predicción guardada en el historial")
    label: str = Field(description="Cultivo recomendado")
    confidence: float = Field(description="Probabilidad de la clase predicha (0-1)")
    top3: list[LabelProb]
    warnings: list[str] = Field(description="Avisos si la entrada está fuera del rango de entrenamiento")
    model_version: int
    created_at: datetime


class PredictionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    input: PredictRequest
    predicted_label: str
    confidence: float
    top3: list[LabelProb]
    model_version: int
    created_at: datetime


class PredictionPage(BaseModel):
    items: list[PredictionItem]
    total: int
    page: int
    size: int


class ClassMetric(BaseModel):
    precision: float
    recall: float
    f1: float
    support: int


class ModelMetrics(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    version: int
    algorithm: str
    trained_at: datetime
    is_active: bool
    n_train: int
    n_test: int
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    cv_f1_mean: float | None
    cv_f1_std: float | None
    classes: list[str]
    confusion_matrix: list[list[int]]
    per_class: dict[str, ClassMetric]
    hyperparams: dict | None


class ModelSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    version: int
    algorithm: str
    trained_at: datetime
    is_active: bool
    n_train: int
    accuracy: float
    f1_macro: float


class RetrainResponse(BaseModel):
    new_version: int
    activated: bool
    reason: str
    previous_version: int | None
    previous_f1_macro: float | None
    metrics: ModelMetrics


class DatasetInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    uploaded_at: datetime
    n_rows: int
    is_active: bool
    notes: str | None


class ValidationReport(BaseModel):
    total_rows: int
    valid_rows: int
    rejected_null_or_non_numeric: int
    rejected_out_of_range: int
    duplicates_removed: int
    classes: int


class UploadResponse(BaseModel):
    dataset: DatasetInfo
    mode: Literal["append", "replace"]
    validation: ValidationReport
    total_active_samples: int
    retrain: RetrainResponse | None = None


class DatasetSummary(BaseModel):
    datasets: list[DatasetInfo]
    total_active_samples: int
    class_distribution: dict[str, int]


class Health(BaseModel):
    status: str
    database: bool
    model_loaded: bool
    active_model_version: int | None
