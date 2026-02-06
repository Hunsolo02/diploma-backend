"""Association table for UserProfile <-> FaceFeature many-to-many relationship."""
from sqlalchemy import Table, Column, ForeignKey

from database import Base

user_profile_face_features = Table(
    "user_profile_face_features",
    Base.metadata,
    Column("user_profile_id", ForeignKey("user_profiles.id", ondelete="CASCADE"), primary_key=True),
    Column("face_feature_id", ForeignKey("face_features.id", ondelete="CASCADE"), primary_key=True),
)
