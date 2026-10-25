-- PostgreSQL schema (mirrors loan_batch/models.py).
-- Run with: psql "$DATABASE_URL" -f sql/schema.sql

CREATE TABLE IF NOT EXISTS payment_batches (
    id              SERIAL PRIMARY KEY,
    batch_id        VARCHAR UNIQUE NOT NULL,
    source_filename VARCHAR,
    payment_date    VARCHAR,
    created_at      TIMESTAMP DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_batches_batch_id ON payment_batches (batch_id);

CREATE TABLE IF NOT EXISTS payments (
    id                     SERIAL PRIMARY KEY,
    batch_id               VARCHAR NOT NULL REFERENCES payment_batches (batch_id),
    payment_id             VARCHAR NOT NULL,
    account_number_masked  VARCHAR,
    amount                 DOUBLE PRECISION,
    expected_amount        DOUBLE PRECISION,
    payment_date           VARCHAR,
    status                 VARCHAR NOT NULL,  -- 'processed' or 'flagged'
    flag_reason            VARCHAR
);
CREATE INDEX IF NOT EXISTS idx_payments_batch_id ON payments (batch_id);
