import uuid

from sqlalchemy import JSON, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class AnalysisSession(Base):
    """Session for phenotype analysis flow (image → questions → answers → result)."""

    __tablename__ = "analysis_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    original_image: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    result: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)

    @staticmethod
    def generate_session_id() -> str:
        return str(uuid.uuid4())
