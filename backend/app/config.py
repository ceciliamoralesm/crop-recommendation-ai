from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
ROOT_DIR = BASE_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    database_url: str = "postgresql+psycopg://crop:crop@localhost:5434/crop_ai"
    models_dir: Path = BASE_DIR / "models"
    seed_csv: Path = ROOT_DIR / "data" / "Crop_recommendation.csv"
    cors_origins: list[str] = ["http://localhost:5174", "http://127.0.0.1:5174"]
    max_upload_mb: int = 10
    # Tolerancia para activar un modelo re-entrenado: se activa si su F1 >= F1_actual - tolerancia
    retrain_tolerance: float = 0.01


settings = Settings()
settings.models_dir.mkdir(parents=True, exist_ok=True)
