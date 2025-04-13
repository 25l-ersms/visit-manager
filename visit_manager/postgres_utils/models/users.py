import uuid

from sqlalchemy import Column, String
from sqlalchemy.orm import Session

from visit_manager.app.models.models import UserCreate
from visit_manager.postgres_utils.models.common import Base


# TODO its just an example
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)


def add_user(db: Session, user: UserCreate) -> User:
    db_user = User(email=str(user.email), full_name=user.full_name)
    db.add(db_user)
    db.commit()
    return db_user


def read_all_users(db: Session) -> list[User]:
    users = db.query(User).all()
    return users
