from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin


class Item(Base, TimestampMixin):
    """Example model - replace with your own models."""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
