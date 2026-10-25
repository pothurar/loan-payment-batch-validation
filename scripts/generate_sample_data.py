"""Generate a larger synthetic payment file (1,000 rows by default).

All data is synthetic: account numbers are made-up 12-digit strings,
names are not included, and no real borrower data is used.
Faults are injected at known rates so the report is interesting:
~2% duplicates, ~2% missing fields, ~3% amount mismatches.

Usage:
    python scripts/generate_sample_data.py --rows 1000 --out data/generated_payments.csv
"""

import argparse
import csv
import random


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=1000)
    parser.add_argument("--out", default="data/generated_payments.csv")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = []
    for i in range(1, args.rows + 1):
        amount = round(rng.uniform(50, 900), 2)
        expected = amount
        account = f"{rng.randint(100000000000, 999999999999)}"
        roll = rng.random()
        if roll < 0.03:
            expected = round(amount + rng.choice([-25.00, 10.00, 50.00]), 2)
        elif roll < 0.05:
            account = ""
        payment_id = f"P{i:05d}"
        if rows and rng.random() < 0.02:
            payment_id = rows[-1]["payment_id"]  # duplicate of previous row
        rows.append(
            {
                "payment_id": payment_id,
                "account_number": account,
                "amount": f"{amount:.2f}",
                "expected_amount": f"{expected:.2f}",
                "payment_date": "2026-01-15",
            }
        )

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["payment_id", "account_number", "amount", "expected_amount", "payment_date"]
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic rows to {args.out}")


if __name__ == "__main__":
    main()
