from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PhenotypeBase(BaseModel):
    view_name: str
    name: str


class PhenotypeCreate(PhenotypeBase):
    pass


class PhenotypeUpdate(BaseModel):
    view_name: str | None = None
    name: str | None = None


class PhenotypeResponse(PhenotypeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
