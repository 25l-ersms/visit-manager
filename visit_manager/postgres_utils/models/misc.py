import enum


class VisitStatus(str, enum.Enum):
    __tablename__ = "visit_status"
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class PaymentStatus(str, enum.Enum):
    __tablename__ = "payment_status"
    processing = "processing"
    cancelled = "cancelled"
    error = "error"
    success = "success"
    refunded = "refunded"
