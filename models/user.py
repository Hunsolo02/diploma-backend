from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """User model for authentication."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
