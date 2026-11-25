"""Tests de integración de la API contra una BD PostgreSQL de pruebas (crop_ai_test).

Requiere:  docker compose up -d   y   docker exec crop_ai_db createdb -U crop crop_ai_test
Ejecutar:  cd backend && python -m pytest -q
"""
import io
import os
import tempfile

os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "postgresql+psycopg://crop:crop@localhost:5434/crop_ai_test")
os.environ["MODELS_DIR"] = tempfile.mkdtemp(prefix="crop_models_")

import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

SAMPLE = {"N": 90, "P": 42, "K": 43, "temperature": 20.88, "humidity": 82.0, "ph": 6.5, "rainfall": 202.9}


@pytest.fixture(scope="module")
def client():
    Base.metadata.drop_all(engine)
    with TestClient(app) as c:  # el lifespan carga el CSV semilla y entrena v1
        yield c


def test_health(client):
    r = client.get("/api/health").json()
    assert r["status"] == "ok" and r["model_loaded"] and r["active_model_version"] == 1


def test_predict_and_history(client):
    r = client.post("/api/predict", json=SAMPLE)
    assert r.status_code == 200
    body = r.json()
    assert body["label"] == "rice"
    assert 0 < body["confidence"] <= 1 and len(body["top3"]) == 3
    hist = client.get("/api/predictions?size=5").json()
    assert hist["total"] >= 1
    assert hist["items"][0]["id"] == body["id"]
    assert hist["items"][0]["input"]["N"] == 90


def test_predict_validation(client):
    bad = {**SAMPLE, "ph": 20}
    assert client.post("/api/predict", json=bad).status_code == 422


def test_predict_out_of_training_range_warns(client):
    r = client.post("/api/predict", json={**SAMPLE, "rainfall": 900}).json()
    assert any("rainfall" in w for w in r["warnings"])


def test_metrics_acceptable(client):
    m = client.get("/api/metrics").json()
    assert m["f1_macro"] >= 0.95  # criterio de éxito definido en CRISP-ML(Q) Fase 1
    assert len(m["classes"]) == 22
    assert len(m["confusion_matrix"]) == 22


def test_upload_rejects_bad_rows_and_retrains(client):
    df = pd.read_csv(settings.seed_csv).sample(110, random_state=0)
    df = df[df["label"].isin(df["label"].value_counts().index)]
    extra = pd.DataFrame([[1, 2, 3, "x", 50, 6, 100, "rice"], [1, 2, 3, 25, 150, 6, 100, "rice"]], columns=df.columns)
    raw = pd.concat([df, extra]).to_csv(index=False).encode()
    r = client.post("/api/datasets/upload", files={"file": ("extra.csv", io.BytesIO(raw), "text/csv")},
                    data={"mode": "append", "retrain": "true"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["validation"]["rejected_null_or_non_numeric"] == 1
    assert body["validation"]["rejected_out_of_range"] == 1
    assert body["retrain"]["new_version"] == 2


def test_upload_missing_columns(client):
    raw = b"a,b\n1,2\n"
    r = client.post("/api/datasets/upload", files={"file": ("x.csv", io.BytesIO(raw), "text/csv")})
    assert r.status_code == 422


def test_retrain_and_rollback(client):
    r = client.post("/api/retrain").json()
    assert r["activated"] is True
    v = r["new_version"]
    assert client.post("/api/models/1/activate").status_code == 200
    assert client.get("/api/health").json()["active_model_version"] == 1
    models = client.get("/api/models").json()
    assert [m["version"] for m in models][:1] == [v]
    assert sum(m["is_active"] for m in models) == 1
