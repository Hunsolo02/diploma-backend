from datetime import datetime
from pydantic import BaseModel, ConfigDict


class FaceFeatureBase(BaseModel):
    view_name: str
    name: str


class FaceFeatureCreate(FaceFeatureBase):
    pass


class FaceFeatureUpdate(BaseModel):
    view_name: str | None = None
    name: str | None = None


class FaceFeatureResponse(FaceFeatureBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
