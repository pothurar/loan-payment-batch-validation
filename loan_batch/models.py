from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from .db import Base


class PaymentBatch(Base):
    """One uploaded payment file.

    Idempotency rule: batch_id is unique. Re-processing the same
    batch_id returns the existing summary instead of inserting the
    payments a second time, so a re-run can never double-count payments.
    """

    __tablename__ = "payment_batches"

    id = Column(Integer, primary_key=True)
    batch_id = Column(String, unique=True, nullable=False, index=True)
    source_filename = Column(String, nullable=True)
    payment_date = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    payments = relationship("Payment", back_populates="batch", cascade="all, delete-orphan")

    @property
    def summary(self) -> dict:
        processed = sum(1 for p in self.payments if p.status == "processed")
        flagged = sum(1 for p in self.payments if p.status == "flagged")
        return {
            "batch_id": self.batch_id,
            "source_filename": self.source_filename,
            "payment_date": self.payment_date,
            "total": len(self.payments),
            "processed": processed,
            "flagged": flagged,
        }


class Payment(Base):
    """One payment row from a batch file.

    account_number is stored masked (last 4 digits only) by the service
    layer before insert, so raw account numbers never land in the DB,
    logs, or API responses.
    """

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    batch_id = Column(String, ForeignKey("payment_batches.batch_id"), nullable=False, index=True)
    payment_id = Column(String, nullable=False)
    account_number_masked = Column(String, nullable=True)
    amount = Column(Float, nullable=True)
    expected_amount = Column(Float, nullable=True)
    payment_date = Column(String, nullable=True)
    status = Column(String, nullable=False)  # "processed" or "flagged"
    flag_reason = Column(String, nullable=True)

    batch = relationship("PaymentBatch", back_populates="payments")
