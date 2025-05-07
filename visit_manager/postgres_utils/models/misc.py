import enum


class VisitStatus(str, enum.Enum):
    """
    pending: Visit is pending and waiting for vendor confirmation
    rejected: Vendor rejected the visit
    confirmed: Visit is confirmed by the vendor, the visit has not started yet
    in_progress: Visit is in progress
    completed: Visit is completed
    client_cancelled: Client cancelled the visit, no matter the previous status
    vendor_cancelled: Vendor cancelled the visit, no matter the previous status
    """

    __tablename__ = "visit_status"
    pending = "pending"
    vendor_rejected = "vendor_rejected"
    client_rejected = "client_rejected"
    confirmed = "confirmed"
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
