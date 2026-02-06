from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin
from models.user_profile_face_feature import user_profile_face_features


class FaceFeature(Base, TimestampMixin):
    __tablename__ = "face_features"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    view_name: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    user_profiles: Mapped[list["UserProfile"]] = relationship(
        "UserProfile",
        secondary=user_profile_face_features,
        back_populates="face_features",
        lazy="selectin",
    )
