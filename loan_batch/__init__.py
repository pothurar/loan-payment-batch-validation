"""Loan Payment Batch Validation & Reporting Service.

Personal project, built with synthetic data only. It is NOT a production
system and was NOT built on a real lender's data.

Pipeline: CSV payment file (S3 or local) -> validation -> PostgreSQL
(or SQLite for local runs) -> SQL reconciliation report -> Flask REST API.
CloudWatch logging/alarms cover failed batches in the AWS deployment.
"""
