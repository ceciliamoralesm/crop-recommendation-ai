"""Modelos ORM. Reflejan exactamente backend/db/schema.sql."""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class FeatureColumns:
    n: Mapped[float] = mapped_column(Float, nullable=False)
    p: Mapped[float] = mapped_column(Float, nullable=False)
    k: Mapped[float] = mapped_column(Float, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    humidity: Mapped[float] = mapped_column(Float, nullable=False)
    ph: Mapped[float] = mapped_column(Float, nullable=False)
    rainfall: Mapped[float] = mapped_column(Float, nullable=False)


class Dataset(Base):
    __tablename__ = "datasets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    n_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(Text)

    samples: Mapped[list["TrainingSample"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")


class TrainingSample(FeatureColumns, Base):
    __tablename__ = "training_samples"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(50), nullable=False)

    dataset: Mapped[Dataset] = relationship(back_populates="samples")


class ModelVersion(Base):
    __tablename__ = "model_versions"
    __table_args__ = (
        Index("ux_model_versions_active", "is_active", unique=True, postgresql_where=text("is_active")),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    algorithm: Mapped[str] = mapped_column(String(100), nullable=False)
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    n_train: Mapped[int] = mapped_column(Integer, nullable=False)
    n_test: Mapped[int] = mapped_column(Integer, nullable=False)
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    precision_macro: Mapped[float] = mapped_column(Float, nullable=False)
    recall_macro: Mapped[float] = mapped_column(Float, nullable=False)
    f1_macro: Mapped[float] = mapped_column(Float, nullable=False)
    cv_f1_mean: Mapped[float | None] = mapped_column(Float)
    cv_f1_std: Mapped[float | None] = mapped_column(Float)
    classes: Mapped[list] = mapped_column(JSONB, nullable=False)
    confusion_matrix: Mapped[list] = mapped_column(JSONB, nullable=False)
    per_class: Mapped[dict] = mapped_column(JSONB, nullable=False)
    hyperparams: Mapped[dict | None] = mapped_column(JSONB)
    model_path: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Prediction(FeatureColumns, Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_versions.id"), nullable=False)
    predicted_label: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    top3: Mapped[list] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    model_version: Mapped[ModelVersion] = relationship()
