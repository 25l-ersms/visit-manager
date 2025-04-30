import enum


class VisitStatus(str, enum.Enum):
    __tablename__ = "visit_status"
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


from visit_manager.postgres_utils.models import PaymentStatus
