"""Command line: process a local CSV and print the reconciliation summary.

Usage:
    python -m loan_batch.cli data/sample_payments.csv --batch-id payments-2026-01-15
    python -m loan_batch.cli data/sample_payments.csv   # batch_id from filename
"""

import argparse
import os
import sys

from .db import Base, make_session_factory
from .service import process_csv_text


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Process a loan payment CSV file.")
    parser.add_argument("csv_file", help="Path to the CSV file to process")
    parser.add_argument("--batch-id", default=None, help="Batch id (default: filename without extension)")
    args = parser.parse_args(argv)

    with open(args.csv_file, encoding="utf-8") as fh:
        csv_text = fh.read()

    batch_id = args.batch_id or os.path.splitext(os.path.basename(args.csv_file.replace("\\", "/")))[0]
    session_factory, engine = make_session_factory()
    Base.metadata.create_all(engine)
    session = session_factory()
    try:
        summary = process_csv_text(session, batch_id, csv_text, source_filename=args.csv_file)
    finally:
        session.close()

    print(f"Batch:      {summary['batch_id']}")
    print(f"Total rows: {summary['total']}")
    print(f"Processed:  {summary['processed']}")
    print(f"Flagged:    {summary['flagged']}")
    print("Run the API and check /batches/<batch_id>/errors to see the flagged rows.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
