import uuid
from visit_manager.postgres_utils.models.models import Visit
from visit_manager.postgres_utils.utils import get_db

async def create_visit(payload: dict) -> None:
    """
    Creates new Visit based on payload dictionary.
    """
    db_gen = get_db()
    session = await anext(db_gen)
    try:
        async with session.begin():
            visit = Visit(
                visit_id=uuid.UUID(payload["visit_id"]),
                client_id=uuid.UUID(payload["client_id"]),
                vendor_id=uuid.UUID(payload["vendor_id"]),
                start_timestamp=payload["start_timestamp"],
                end_timestamp=payload["end_timestamp"],
                description=payload["description"],
                service_type_id=uuid.UUID(payload["service_type_id"]),
                address_id=uuid.UUID(payload["address_id"]),
                status=payload.get("status", "pending"),
            )
            session.add(visit)
    finally:
        await db_gen.aclose()
