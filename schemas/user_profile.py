import base64
from pydantic import BaseModel, ConfigDict


class UserProfileBase(BaseModel):
    region_id: int
    phenotype_analyze: dict | list | None = None


class UserProfileCreate(UserProfileBase):
    """Create with base64-encoded images (optional)."""
    original_image_base64: str | None = None
    analyzed_image_base64: str | None = None
    face_feature_ids: list[int] = []


class UserProfileUpdate(BaseModel):
    region_id: int | None = None
    phenotype_analyze: dict | list | None = None
    original_image_base64: str | None = None
    analyzed_image_base64: str | None = None
    face_feature_ids: list[int] | None = None


class FaceFeatureRef(BaseModel):
    id: int
    view_name: str
    name: str


class UserProfileResponse(UserProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_image_base64: str | None = None
    analyzed_image_base64: str | None = None
    create_time: int
    update_time: int
    face_features: list[FaceFeatureRef] = []


def profile_to_response(profile) -> dict:
    """Convert UserProfile ORM to response dict with base64-encoded images and face_features."""
    face_features = getattr(profile, "face_features", []) or []
    return {
        "id": profile.id,
        "region_id": profile.region_id,
        "phenotype_analyze": profile.phenotype_analyze,
        "original_image_base64": (
            base64.b64encode(profile.original_image).decode()
            if profile.original_image else None
        ),
        "analyzed_image_base64": (
            base64.b64encode(profile.analyzed_image).decode()
            if profile.analyzed_image else None
        ),
        "create_time": profile.create_time,
        "update_time": profile.update_time,
        "face_features": [
            {"id": f.id, "view_name": f.view_name, "name": f.name}
            for f in face_features
        ],
    }
