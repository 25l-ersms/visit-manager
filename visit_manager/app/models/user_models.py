from enum import Enum

from pydantic import BaseModel, EmailStr
import datetime


class ServiceTypeEnum(Enum):
    ELECTRICIAN = "electrician"
    PLUMBER = "plumber"
    CARPENTER = "carpenter"
    PAINTER = "painter"
    CLEANER = "cleaner"


class AddressCreate(BaseModel):
    latitude: float
    longitude: float
    street: str
    city: str
    state_or_region: str
    country: str
    zip_code: str


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str


class UserSessionData(BaseModel):
    user_id: str
    user_email: str


class VendorCreate(BaseModel):
    vendor_name: str
    address: AddressCreate
    phone_number: str
    service_types: list[ServiceTypeEnum]


class ClientCreate(BaseModel):
    phone_number: str
    address: AddressCreate

class VisitCreate(BaseModel):
    start_time: datetime.datetime
    end_time: datetime.datetime
    vendor_email: str


class VisitData:
    old_visit: VisitCreate
    future_visit: VisitCreate


class UserInfoModel(BaseModel):
    first_name: str
    last_name: str
    email: str
    user_type: str