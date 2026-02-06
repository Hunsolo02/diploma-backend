from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.region import Region
from schemas.region import RegionCreate, RegionUpdate, RegionResponse

router = APIRouter(prefix="/regions", tags=["regions"])


@router.get("/", response_model=list[RegionResponse])
def list_regions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    regions = db.query(Region).offset(skip).limit(limit).all()
    return regions


@router.post("/", response_model=RegionResponse)
def create_region(region: RegionCreate, db: Session = Depends(get_db)):
    db_region = Region(**region.model_dump())
    db.add(db_region)
    db.commit()
    db.refresh(db_region)
    return db_region


@router.get("/{region_id}", response_model=RegionResponse)
def get_region(region_id: int, db: Session = Depends(get_db)):
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return region


@router.patch("/{region_id}", response_model=RegionResponse)
def update_region(region_id: int, region_update: RegionUpdate, db: Session = Depends(get_db)):
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    update_data = region_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(region, key, value)
    db.commit()
    db.refresh(region)
    return region


@router.delete("/{region_id}", status_code=204)
def delete_region(region_id: int, db: Session = Depends(get_db)):
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    db.delete(region)
    db.commit()
