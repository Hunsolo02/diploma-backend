from datetime import datetime
from pydantic import BaseModel, ConfigDict


class RegionBase(BaseModel):
    view_name: str
    name: str


class RegionCreate(RegionBase):
    pass


class RegionUpdate(BaseModel):
    view_name: str | None = None
    name: str | None = None


class RegionResponse(RegionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
