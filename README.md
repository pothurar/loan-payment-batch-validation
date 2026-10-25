# Loan Payment Batch Validation & Reporting Service

**Personal project, synthetic data only.** This is not a production system,
and it was not built on a real lender's data. All payment files in
`data/` are made-up examples.

## What it does

A daily loan payment file arrives as a CSV, gets validated, and produces
a reconciliation report — the same shape of problem a production-support /
application-support engineer meets every day:

```
CSV file (S3 or local)
      |
      v
  Validation: missing field | duplicate payment_id | amount mismatch | bad amount
      |
      v
  PostgreSQL (or SQLite locally): payment_batches + payments
      |  account numbers stored MASKED (last 4 digits only)
      v
  SQL reconciliation report: processed / flagged per batch, per day
      |
      v
  Flask REST API: batch status, error lookup, daily report
  AWS: S3 upload -> Lambda -> CloudWatch logs + alarm on failed batches
```

## Validation rules

| Flag | Meaning |
|---|---|
| `missing_field` | Any of payment_id, account_number, amount, expected_amount, payment_date is blank |
| `duplicate_payment_id` | Same payment_id twice in one batch — a payment must count exactly once |
| `amount_mismatch` | `amount` differs from `expected_amount` (the scheduled amount) by even 1 cent |
| `invalid_amount` | amount / expected_amount is not a number |

Flagged rows are stored with their reason and are **not** counted as
processed. Re-processing the same `batch_id` is idempotent: it returns
the existing summary and inserts nothing again, so a re-run can never
double-count payments.

## Quick start (local, no AWS, no Postgres server needed)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-cov

# 1. Process the sample file (20 rows: 16 clean, 4 flagged)
python -m loan_batch.cli data/sample_payments.csv --batch-id sample-2026-01-15
# Expected: Total rows: 20, Processed: 16, Flagged: 4

# 2. Start the API (uses the same loan_batches.db file)
python -m loan_batch.api
# Then:
curl http://127.0.0.1:5000/batches
curl http://127.0.0.1:5000/batches/sample-2026-01-15/errors
curl "http://127.0.0.1:5000/reports/daily?date=2026-01-15"

# 3. Run the tests with coverage
pytest --cov=loan_batch --cov-report=term-missing -q
```

Sample file breakdown (verify it yourself): P005 and P017 are amount
mismatches, P007 has a missing account number, and P002 appears twice
(the second copy is the duplicate). 20 − 4 = 16 processed.

## API

| Method | Endpoint | Returns |
|---|---|---|
| GET | `/health` | `{"status": "ok"}` |
| GET | `/batches` | All batch summaries |
| GET | `/batches/<batch_id>` | One batch summary |
| GET | `/batches/<batch_id>/errors` | Flagged rows only, masked account numbers |
| GET | `/reports/daily?date=YYYY-MM-DD` | Reconciliation report for that date |

Raw account numbers never appear in API responses: the service masks
them (`123456789012` -> `********9012`) before inserting into the DB.

## Using PostgreSQL (instead of the default SQLite)

```bash
# Example with Docker:
docker run -d --name loan-postgres -e POSTGRES_PASSWORD=devpass \
  -e POSTGRES_DB=loan_batches -p 5432:5432 postgres:16

export DATABASE_URL="postgresql+psycopg2://postgres:devpass@localhost:5432/loan_batches"
# Or apply the DDL directly:
psql "$DATABASE_URL" -f sql/schema.sql
```

Tests deliberately use in-memory SQLite so they run anywhere with no
server. That split is stated here, not hidden: app code is SQLAlchemy
and database-agnostic, and `sql/schema.sql` is the PostgreSQL DDL.
The raw daily-report query is in `sql/reconciliation.sql`.

## Larger synthetic data

```bash
python scripts/generate_sample_data.py --rows 1000 --out data/generated_payments.csv
python -m loan_batch.cli data/generated_payments.csv --batch-id generated-2026-01-15
```

## Deploying to AWS (your own account)

`template.yaml` is an AWS SAM template: S3 input bucket -> Lambda
(`loan_batch.lambda_handler.handler`) -> RDS PostgreSQL, with a
CloudWatch alarm on Lambda errors. Deploy it yourself in your own
account — never commit real credentials, use Secrets Manager for the
DB password in a real deployment, and put the DB in private subnets.
The Lambda handler calls the exact same `process_s3_object()` used
locally, so local and deployed behaviour cannot drift apart. Its IAM
policy is least-privilege: S3 read from the input bucket only, plus
CloudWatch Logs.

## Project structure

```
loan_batch/
  validator.py      # row rules: missing / duplicate / mismatch / bad amount
  masking.py        # account-number masking (last 4 digits)
  models.py         # payment_batches + payments (SQLAlchemy)
  service.py        # process_csv_text, process_s3_object, daily_reconciliation
  api.py            # Flask app: batches, errors, daily report
  lambda_handler.py # S3 event -> process_s3_object, CloudWatch logging
  cli.py            # python -m loan_batch.cli <file.csv>
  config.py         # DATABASE_URL / S3_BUCKET env vars
tests/              # validator, masking, service, API (pytest + coverage)
sql/                # schema.sql (PostgreSQL DDL), reconciliation.sql
data/               # sample_payments.csv (20 rows, synthetic)
scripts/            # generate_sample_data.py (1,000 synthetic rows)
.github/workflows/  # ci.yml: install, pytest --cov, sample-file smoke test
template.yaml       # AWS SAM: S3 -> Lambda -> RDS + CloudWatch alarm
```

## Interview study guide — read this before claiming the project

If you put this on a resume, you must be able to answer these
without notes:

1. **What is the duplicate key, and why?** payment_id alone, within
   one batch — a payment must be processed exactly once per batch.
2. **What is an amount mismatch checked against?** `expected_amount`,
   the scheduled amount in the file. A mismatch means file and
   schedule disagree; the payment is flagged, not silently accepted.
3. **How does Lambda get triggered?** An S3 ObjectCreated event on
   the input bucket; the handler downloads the object with boto3 and
   calls the same processing function used locally.
4. **Where does PostgreSQL run, and what does SQLite do?** SQLite is
   only the local default and the test database. Production here
   means PostgreSQL (RDS in `template.yaml`, Docker locally).
5. **How is a re-run prevented from double-counting?** batch_id is
   unique; an existing batch returns its summary with no new inserts.
6. **Where do raw account numbers go?** Nowhere. They are masked
   before insert, so logs, the DB, and API responses only ever see
   the last 4 digits.
7. **How is 85%+ test coverage actually measured?** `pytest --cov`
   (pytest-cov). Run it, read the missing-lines report, and do not
   quote a coverage number you have not just reproduced.

Spend 8-12 hours of your own time on this before an interview:
run it, break a CSV row on purpose, add a validation rule, change
the duplicate logic, deploy the Lambda trigger (or at least walk
through `template.yaml` line by line), and re-run the tests. A
project you cannot change is a project you did not build.
