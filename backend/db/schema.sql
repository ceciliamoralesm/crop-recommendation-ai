-- =====================================================================
-- Crop Recommendation AI - Esquema de base de datos (PostgreSQL)
-- Se ejecuta automáticamente al crear el contenedor (docker-entrypoint-initdb.d)
-- o manualmente:  psql -U crop -d crop_ai -f schema.sql
-- =====================================================================

CREATE TABLE IF NOT EXISTS datasets (
    id           SERIAL PRIMARY KEY,
    filename     VARCHAR(255) NOT NULL,
    uploaded_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    n_rows       INTEGER      NOT NULL CHECK (n_rows >= 0),
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
    notes        TEXT
);

CREATE TABLE IF NOT EXISTS training_samples (
    id           BIGSERIAL PRIMARY KEY,
    dataset_id   INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    n            DOUBLE PRECISION NOT NULL CHECK (n >= 0),
    p            DOUBLE PRECISION NOT NULL CHECK (p >= 0),
    k            DOUBLE PRECISION NOT NULL CHECK (k >= 0),
    temperature  DOUBLE PRECISION NOT NULL,
    humidity     DOUBLE PRECISION NOT NULL CHECK (humidity BETWEEN 0 AND 100),
    ph           DOUBLE PRECISION NOT NULL CHECK (ph BETWEEN 0 AND 14),
    rainfall     DOUBLE PRECISION NOT NULL CHECK (rainfall >= 0),
    label        VARCHAR(50) NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_training_samples_dataset ON training_samples(dataset_id);

CREATE TABLE IF NOT EXISTS model_versions (
    id               SERIAL PRIMARY KEY,
    version          INTEGER      NOT NULL UNIQUE,
    algorithm        VARCHAR(100) NOT NULL,
    trained_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    n_train          INTEGER      NOT NULL,
    n_test           INTEGER      NOT NULL,
    accuracy         DOUBLE PRECISION NOT NULL,
    precision_macro  DOUBLE PRECISION NOT NULL,
    recall_macro     DOUBLE PRECISION NOT NULL,
    f1_macro         DOUBLE PRECISION NOT NULL,
    cv_f1_mean       DOUBLE PRECISION,
    cv_f1_std        DOUBLE PRECISION,
    classes          JSONB        NOT NULL,
    confusion_matrix JSONB        NOT NULL,
    per_class        JSONB        NOT NULL,
    hyperparams      JSONB,
    model_path       VARCHAR(500) NOT NULL,
    is_active        BOOLEAN      NOT NULL DEFAULT FALSE
);
-- Solo un modelo activo a la vez
CREATE UNIQUE INDEX IF NOT EXISTS ux_model_versions_active
    ON model_versions(is_active) WHERE is_active;

CREATE TABLE IF NOT EXISTS predictions (
    id                BIGSERIAL PRIMARY KEY,
    model_version_id  INTEGER NOT NULL REFERENCES model_versions(id),
    n                 DOUBLE PRECISION NOT NULL,
    p                 DOUBLE PRECISION NOT NULL,
    k                 DOUBLE PRECISION NOT NULL,
    temperature       DOUBLE PRECISION NOT NULL,
    humidity          DOUBLE PRECISION NOT NULL,
    ph                DOUBLE PRECISION NOT NULL,
    rainfall          DOUBLE PRECISION NOT NULL,
    predicted_label   VARCHAR(50) NOT NULL,
    confidence        DOUBLE PRECISION NOT NULL,
    top3              JSONB NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_predictions_created ON predictions(created_at DESC);
