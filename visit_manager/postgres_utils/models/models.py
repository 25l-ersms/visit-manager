import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import CheckConstraint, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy_utils import EmailType, PhoneNumber, PhoneNumberType

from visit_manager.postgres_utils.models.common import Base
from visit_manager.postgres_utils.models.misc import PaymentStatus, VisitStatus


class User(Base):
    __tablename__ = "user"

    user_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    first_name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(EmailType, unique=True, index=True, nullable=False)
    registration_timestamp: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    last_login: Mapped[datetime] = mapped_column(server_default=func.now())
    admin_profile: Mapped[Optional["Admin"]] = relationship(
        back_populates="user",
        uselist=False,
        single_parent=True,
        primaryjoin="User.user_id==Admin.admin_id",
        lazy="joined",
    )
    vendor_profile: Mapped[Optional["Vendor"]] = relationship(
        back_populates="user",
        uselist=False,
        single_parent=True,
        primaryjoin="User.user_id==Vendor.vendor_id",
        lazy="joined",
    )
    client_profile: Mapped[Optional["Client"]] = relationship(
        back_populates="user",
        uselist=False,
        single_parent=True,
        primaryjoin="User.user_id==Client.client_id",
        lazy="joined",
    )


class Admin(Base):
    __tablename__ = "admin"
    admin_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.user_id"), primary_key=True)
    user: Mapped["User"] = relationship(
        back_populates="admin_profile", single_parent=True, primaryjoin="User.user_id==Admin.admin_id", lazy="joined"
    )


class Client(Base):
    __tablename__ = "client"
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.user_id"), primary_key=True)
    user: Mapped["User"] = relationship(
        back_populates="client_profile", single_parent=True, primaryjoin="User.user_id==Client.client_id", lazy="joined"
    )
    registration_fee_payment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("payment.payment_id"), unique=True, nullable=True, index=True
    )
    registration_fee_payment: Mapped[Optional["Payment"]] = relationship(single_parent=True)
    phone_number: Mapped[PhoneNumber] = mapped_column(PhoneNumberType, nullable=False)
    is_active: Mapped[bool] = mapped_column(server_default="true", nullable=False)
    visits: Mapped[List["Visit"]] = relationship(back_populates="client")


class Vendor(Base):
    __tablename__ = "vendor"
    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.user_id"), primary_key=True)
    user: Mapped["User"] = relationship(
        back_populates="vendor_profile", single_parent=True, primaryjoin="User.user_id==Vendor.vendor_id", lazy="joined"
    )
    vendor_name: Mapped[str] = mapped_column(nullable=False)
    required_deposit_gr: Mapped[Optional[int]] = mapped_column(
        CheckConstraint("required_deposit_gr IS NULL OR required_deposit_gr > 0")
    )
    registration_fee_payment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("payment.payment_id"), nullable=True, unique=True, index=True
    )
    registration_fee_payment: Mapped[Optional["Payment"]] = relationship(single_parent=True)
    address_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("address.address_id"), nullable=False, unique=True, index=True
    )
    address: Mapped[Optional["Address"]] = relationship(single_parent=True)
    phone_number: Mapped[PhoneNumber] = mapped_column(PhoneNumberType, nullable=False)
    is_active: Mapped[bool] = mapped_column(server_default="true", nullable=False)
    offered_service_types: Mapped[List["ServiceType"]] = relationship(
        secondary="vendor_offered_service_types", back_populates="offering_vendors"
    )
    visits: Mapped[List["Visit"]] = relationship(back_populates="vendor")

    def to_dict(self) -> dict:
        """Convert vendor instance to a dictionary including relationships."""
        result = super().to_dict()
        # Add user info
        if self.user:
            result["user"] = {
                "email": self.user.email,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
            }
        # Add address info
        if self.address:
            result["address"] = self.address.to_dict()
        # Add service types
        result["service_types"] = [
            {"name": st.name, "description": st.description} for st in self.offered_service_types
        ]
        # Remove sensitive or unnecessary fields
        result.pop("registration_fee_payment_id", None)
        return result


class Address(Base):
    __tablename__ = "address"
    address_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    street: Mapped[str] = mapped_column(nullable=False)
    city: Mapped[str] = mapped_column(nullable=False)
    state_or_region: Mapped[str] = mapped_column(nullable=False)
    country: Mapped[str] = mapped_column(nullable=False)
    zip_code: Mapped[str] = mapped_column(nullable=False)

    def to_dict(self) -> dict:
        """Convert address instance to a dictionary."""
        result = super().to_dict()
        # Remove unnecessary fields
        result.pop("address_id", None)
        return result


class Payment(Base):
    __tablename__ = "payment"
    payment_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    stripe_charge_id: Mapped[str] = mapped_column(unique=True, index=True)
    amount: Mapped[int] = mapped_column(CheckConstraint("amount > 0"), nullable=False)
    currency: Mapped[str] = mapped_column(nullable=False, default="pln")
    transaction_timestamp: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus, name="payment_status"), nullable=False)


class ChatSession(Base):
    __tablename__ = "chat_session"
    __table_args__ = (UniqueConstraint("visit_id", "user_id", "vendor_id"),)
    chat_session_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.user_id"), nullable=False, index=True)
    user: Mapped["User"] = relationship(single_parent=True)
    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendor.vendor_id"), nullable=False, index=True)
    vendor: Mapped["Vendor"] = relationship(single_parent=True)
    visit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("visit.visit_id"), nullable=True, index=True)
    visit: Mapped["Visit"] = relationship(back_populates="chat_session", single_parent=True)


class ServiceType(Base):
    __tablename__ = "service_type"
    service_type_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    description: Mapped[str] = mapped_column(nullable=False)
    offering_vendors: Mapped[List["Vendor"]] = relationship(
        secondary="vendor_offered_service_types", back_populates="offered_service_types"
    )


class VendorOfferedServiceTypes(Base):
    __tablename__ = "vendor_offered_service_types"
    __table_args__ = (UniqueConstraint("vendor_id", "service_type_id"),)
    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendor.vendor_id"), primary_key=True)
    service_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("service_type.service_type_id"), primary_key=True)


class Visit(Base):
    __tablename__ = "visit"
    visit_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("client.client_id"), nullable=False, index=True)
    client: Mapped["Client"] = relationship(back_populates="visits", single_parent=True)
    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendor.vendor_id"), nullable=False, index=True)
    vendor: Mapped["Vendor"] = relationship(back_populates="visits", single_parent=True)
    start_timestamp: Mapped[datetime] = mapped_column(nullable=False)
    end_timestamp: Mapped[datetime] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    service_type_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("service_type.service_type_id"), nullable=False, index=True
    )
    service_type: Mapped["ServiceType"] = relationship(single_parent=True)
    address_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("address.address_id"), nullable=False, index=True)
    address: Mapped["Address"] = relationship(single_parent=True)
    deposit_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("payment.payment_id"), nullable=True, unique=True, index=True
    )
    deposit: Mapped[Optional["Payment"]] = relationship(single_parent=True)
    verification_code: Mapped[Optional[str]] = mapped_column(nullable=True)
    review_opinion_score: Mapped[Optional[int]] = mapped_column(
        CheckConstraint("review_opinion_score IS NULL OR review_opinion_score >= 1 AND review_opinion_score <= 5"),
        CheckConstraint("(status = 'completed' AND review_opinion_score IS NOT NULL) OR review_opinion_score IS NULL"),
    )
    review_comment: Mapped[Optional[str]] = mapped_column(nullable=True)
    status: Mapped[VisitStatus] = mapped_column(Enum(VisitStatus, name="visit_status"), nullable=False)
    description_attachments: Mapped[List["Attachment"]] = relationship(
        secondary="visit_description_attachment", cascade="all, delete-orphan", single_parent=True
    )
    review_attachments: Mapped[List["Attachment"]] = relationship(
        secondary="visit_review_attachment", cascade="all, delete-orphan", single_parent=True
    )
    chat_session: Mapped[Optional["ChatSession"]] = relationship(
        back_populates="visit", uselist=False, single_parent=True
    )


class Attachment(Base):
    __tablename__ = "attachment"
    attachment_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    object_uri: Mapped[str] = mapped_column(nullable=False)
    creation_timestamp: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    modification_timestamp: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )


class VisitDescriptionAttachment(Base):
    __tablename__ = "visit_description_attachment"
    __table_args__ = (UniqueConstraint("visit_id", "attachment_id"),)
    visit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("visit.visit_id"), primary_key=True)
    attachment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("attachment.attachment_id"), primary_key=True)


class VisitReviewAttachment(Base):
    __tablename__ = "visit_review_attachment"
    __table_args__ = (UniqueConstraint("visit_id", "attachment_id"),)
    visit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("visit.visit_id"), primary_key=True)
    attachment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("attachment.attachment_id"), primary_key=True)
