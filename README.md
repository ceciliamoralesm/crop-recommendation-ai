# 🌱 Recomendador de Cultivos con IA

Sistema de aprendizaje supervisado (**clasificación multiclase, 22 cultivos**) que recomienda qué sembrar según el suelo (N, P, K, pH) y el clima (temperatura, humedad, lluvia). Se desarrolló siguiendo la metodología **CRISP-ML(Q)**.

- **Modelo:** StandardScaler + RandomForest, con **F1 macro de 0.9955** en test y 0.995 ± 0.005 en CV de 5 folds
- **Servicio de IA:** Python · FastAPI · SQLAlchemy · PostgreSQL
- **Cliente web:** React + Vite
- **Dataset:** [Crop Recommendation (Kaggle)](https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset)

```
Jupyter (EDA) ─► Servicio IA (FastAPI + scikit-learn) ◄── REST ──► Cliente web (React)
                         │
                         ▼
                    PostgreSQL
```

## Estructura

```
├── data/Crop_recommendation.csv       # Dataset semilla
├── notebooks/01_eda_y_entrenamiento.ipynb   # CRISP-ML(Q) fases 1-4: EDA, comparación de modelos, evaluación
├── backend/                           # Servicio de IA (API REST)
│   ├── app/                           # FastAPI: main, ml, services, routers, ORM
│   ├── db/schema.sql                  # Script de generación de la BD
│   └── tests/                         # Tests de integración (pytest)
├── frontend/                          # Cliente web React
├── docs/
│   ├── documento_crisp_ml_q.md        # Documento principal (CRISP-ML(Q) y desarrollo)
│   ├── diagrama_bd.md                 # Diagrama ER y decisiones de diseño
│   ├── openapi.json · swagger.yaml    # Documento Swagger de la API
│   ├── guion_video.md                 # Guion del video demostrativo
│   └── revision_pr_ia.md              # Cómo obtener la evidencia de revisión de PR con IA
├── entrega/                           # Documentos finales en Word y PDF + checklist
└── docker-compose.yml                 # PostgreSQL
```

## Puesta en marcha

Requisitos: Python 3.11 o superior, Node 20 o superior y Docker.

```bash
# 1. Base de datos (crea las tablas con backend/db/schema.sql)
docker compose up -d

# 2. Servicio de IA
python -m venv .venv
.venv\Scripts\activate            # Linux/Mac: source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
copy .env.example .env            # Linux/Mac: cp .env.example .env
uvicorn app.main:app --port 8001
# Al primer arranque carga el CSV en la BD y entrena el modelo v1.
# Swagger: http://127.0.0.1:8001/docs

# 3. Cliente web (en otra terminal)
cd frontend
copy .env.example .env
npm install
npm run dev                       # http://localhost:5174
```

> Puertos: PostgreSQL **5434**, API **8001** y web **5174**, elegidos para no chocar con otros proyectos. Se cambian en `docker-compose.yml`, `backend/.env` y `frontend/.env`.

## Endpoints

| Método | Ruta | Uso |
|---|---|---|
| POST | `/api/predict` | Enviar datos y obtener el cultivo recomendado, la confianza y el top 3 |
| GET | `/api/predictions` | Historial de predicciones (paginado y filtrable) |
| GET | `/api/metrics` | Métricas del modelo activo o de una versión concreta |
| POST | `/api/retrain` | Re-entrenar con los datos activos (con puerta de calidad) |
| POST | `/api/datasets/upload` | Subir un CSV de entrenamiento (append o replace, re-entrenamiento opcional) |
| GET | `/api/models` · POST `/api/models/{v}/activate` | Versiones del modelo y rollback |
| GET | `/api/datasets` · PATCH `/api/datasets/{id}` · GET `/api/datasets/template` | Gestión de los datos |
| GET | `/api/health` | Estado del servicio |

Documentación completa en `http://127.0.0.1:8001/docs` o en [`docs/openapi.json`](docs/openapi.json).

## Tests

```bash
docker exec crop_ai_db createdb -U crop crop_ai_test   # solo la primera vez
cd backend
python -m pytest -q
```

## Reproducir el entrenamiento

```bash
pip install jupyter matplotlib seaborn
jupyter lab notebooks/01_eda_y_entrenamiento.ipynb
```
