import json
from typing import Sequence

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import StatementError
from sqlalchemy.ext.asyncio import AsyncSession

from visit_manager.app.models.user_models import ServiceTypeEnum, UserCreate, UserSessionData, VendorCreate
from visit_manager.kafka_utils.common import KafkaTopics
from visit_manager.kafka_utils.producer import send_message
from visit_manager.package_utils.logger_conf import logger
from visit_manager.postgres_utils.consts import DEPOSIT_GR
from visit_manager.postgres_utils.models.models import Address, ServiceType, User, Vendor


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_or_update_user(session: AsyncSession, user: UserCreate) -> User:
    logger.info(f"Creating or updating user: {user.email}")
    existing_user = await get_user_by_email(session, user.email)
    if existing_user:
        return existing_user
    # Split full_name into first_name and last_name, defaulting to the full value if can't split
    name_parts = user.full_name.split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else name_parts[0]

    db_user = User(email=str(user.email), first_name=first_name, last_name=last_name)
    session.add(db_user)
    await session.flush()
    return db_user


async def read_all_users(session: AsyncSession) -> Sequence[User]:
    result = await session.execute(select(User))
    users = result.scalars().all()
    return users


async def get_service_types_by_name(
    session: AsyncSession, service_type_names: list[ServiceTypeEnum]
) -> list[ServiceType]:
    # Convert enum values to strings
    service_type_str_names = [st.value for st in service_type_names]
    result = await session.execute(select(ServiceType).where(ServiceType.name.in_(service_type_str_names)))
    service_types = result.scalars().all()
    if len(service_types) != len(service_type_names):
        raise HTTPException(status_code=404, detail="Incorrect service types")
    return service_types


async def register_as_vendor(session: AsyncSession, user_session_data: UserSessionData, vendor_data: VendorCreate):
    user = await get_user_by_email(session, user_session_data.user_email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.vendor_profile is not None:
        raise HTTPException(status_code=400, detail="User is already a vendor")

    service_types = await get_service_types_by_name(session, vendor_data.service_types)

    # Create Address object first
    address = Address(
        latitude=vendor_data.address.latitude,
        longitude=vendor_data.address.longitude,
        street=vendor_data.address.street,
        city=vendor_data.address.city,
        state_or_region=vendor_data.address.state_or_region,
        country=vendor_data.address.country,
        zip_code=vendor_data.address.zip_code,
    )
    session.add(address)
    await session.flush()  # Flush to get the address_id

    vendor = Vendor(
        vendor_id=user.user_id,
        vendor_name=vendor_data.vendor_name,
        phone_number=vendor_data.phone_number,
        address_id=address.address_id,
        required_deposit_gr=DEPOSIT_GR,
        offered_service_types=service_types,
    )
    try:
        session.add(vendor)
        await session.flush()
    except StatementError as e:
        logger.error(f"Error creating vendor: {e}")
        raise HTTPException(status_code=400, detail="Incorrect phone number")

    # Send serialized vendor data to Kafka
    send_message(json.dumps(vendor.to_dict()), KafkaTopics.USERS)
    return vendor
