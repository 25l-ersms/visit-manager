import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy_utils import PhoneNumber


class Base(AsyncAttrs, DeclarativeBase):
    def to_dict(self) -> dict:
        """Convert model instance to a dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # Handle special types
            if isinstance(value, uuid.UUID):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, PhoneNumber):
                value = str(value)
            result[column.name] = value
        return result
