"""Flask REST API: batch status, error lookup, daily reconciliation.

Endpoints:
    GET  /health
    GET  /batches
    GET  /batches/<batch_id>
    GET  /batches/<batch_id>/errors
    GET  /reports/daily?date=YYYY-MM-DD

Error responses never include raw account numbers: the database only
stores masked account numbers, so the API cannot leak them.
"""

from flask import Flask, jsonify, request

from .db import Base, make_session_factory
from .service import daily_reconciliation


def _payment_to_dict(payment) -> dict:
    return {
        "payment_id": payment.payment_id,
        "account_number_masked": payment.account_number_masked,
        "amount": payment.amount,
        "expected_amount": payment.expected_amount,
        "payment_date": payment.payment_date,
        "status": payment.status,
        "flag_reason": payment.flag_reason,
    }


def create_app(session_factory=None, engine=None):
    from .models import Payment, PaymentBatch  # noqa: F401  (register models)

    if session_factory is None:
        session_factory, engine = make_session_factory()
    if engine is not None:
        Base.metadata.create_all(engine)

    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/batches")
    def list_batches():
        session = session_factory()
        try:
            batches = session.query(PaymentBatch).order_by(PaymentBatch.batch_id).all()
            return jsonify([b.summary for b in batches])
        finally:
            session.close()

    @app.get("/batches/<batch_id>")
    def get_batch(batch_id: str):
        session = session_factory()
        try:
            batch = session.query(PaymentBatch).filter_by(batch_id=batch_id).first()
            if batch is None:
                return jsonify({"error": "batch not found"}), 404
            return jsonify(batch.summary)
        finally:
            session.close()

    @app.get("/batches/<batch_id>/errors")
    def get_batch_errors(batch_id: str):
        session = session_factory()
        try:
            batch = session.query(PaymentBatch).filter_by(batch_id=batch_id).first()
            if batch is None:
                return jsonify({"error": "batch not found"}), 404
            flagged = (
                session.query(Payment)
                .filter_by(batch_id=batch_id, status="flagged")
                .order_by(Payment.payment_id)
                .all()
            )
            return jsonify([_payment_to_dict(p) for p in flagged])
        finally:
            session.close()

    @app.get("/reports/daily")
    def daily_report():
        date = request.args.get("date")
        if not date:
            return jsonify({"error": "query parameter 'date' is required, e.g. ?date=2026-01-15"}), 400
        session = session_factory()
        try:
            return jsonify(daily_reconciliation(session, date))
        finally:
            session.close()

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=True)
