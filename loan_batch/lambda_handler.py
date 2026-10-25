"""AWS Lambda entry point: S3 upload -> validate -> PostgreSQL.

Trigger (see template.yaml): an object created in the input S3 bucket.
What Lambda does on each event:
  1. Reads bucket + key from the S3 event.
  2. Downloads the CSV with boto3.
  3. Runs the same process_s3_object() used locally, so local and
     deployed behaviour cannot drift apart.
  4. Logs the summary (CloudWatch Logs). A CloudWatch alarm on
     Lambda errors / failed batches is defined in template.yaml.

IAM (least privilege, see template.yaml): the Lambda role may only
GetObject from the input bucket, write logs, and connect to the RDS
database. It has no S3 write, no IAM, and no other AWS permissions.
"""

import logging
import os

import boto3

from .db import Base, make_session_factory
from .service import process_s3_object

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event, context):
    session_factory, engine = make_session_factory()
    Base.metadata.create_all(engine)
    session = session_factory()
    s3_client = boto3.client("s3")
    results = []
    try:
        for record in event.get("Records", []):
            s3 = record["s3"]
            bucket = s3["bucket"]["name"]
            key = s3["object"]["key"]
            summary = process_s3_object(session, s3_client, bucket, key)
            logger.info("processed s3://%s/%s -> %s", bucket, key, summary)
            results.append(summary)
        return {"processed": results}
    finally:
        session.close()
