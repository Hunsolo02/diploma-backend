from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin


class AnalysisQuestion(Base, TimestampMixin):
    """Configurable question for the analysis questionnaire."""

    __tablename__ = "analysis_questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # "text" | "select" | "number"
    options: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)  # for select type
