import time

from sqlalchemy import ForeignKey, Integer, LargeBinary, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.user_profile_face_feature import user_profile_face_features


def unix_timestamp() -> int:
    return int(time.time())


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id"), nullable=False)
    phenotype_analyze: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    original_image: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    analyzed_image: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    create_time: Mapped[int] = mapped_column(Integer, default=unix_timestamp)
    update_time: Mapped[int] = mapped_column(Integer, default=unix_timestamp, onupdate=unix_timestamp)

    face_features: Mapped[list["FaceFeature"]] = relationship(
        "FaceFeature",
        secondary=user_profile_face_features,
        back_populates="user_profiles",
        lazy="selectin",
    )
