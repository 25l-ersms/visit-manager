from enum import Enum

from pydantic import BaseModel, EmailStr


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
