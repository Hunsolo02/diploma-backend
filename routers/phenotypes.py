from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.phenotype import Phenotype
from schemas.phenotype import PhenotypeCreate, PhenotypeUpdate, PhenotypeResponse

router = APIRouter(prefix="/phenotypes", tags=["phenotypes"])


@router.get("/", response_model=list[PhenotypeResponse])
def list_phenotypes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    phenotypes = db.query(Phenotype).offset(skip).limit(limit).all()
    return phenotypes


@router.post("/", response_model=PhenotypeResponse)
def create_phenotype(phenotype: PhenotypeCreate, db: Session = Depends(get_db)):
    db_phenotype = Phenotype(**phenotype.model_dump())
    db.add(db_phenotype)
    db.commit()
    db.refresh(db_phenotype)
    return db_phenotype


@router.get("/{phenotype_id}", response_model=PhenotypeResponse)
def get_phenotype(phenotype_id: int, db: Session = Depends(get_db)):
    phenotype = db.query(Phenotype).filter(Phenotype.id == phenotype_id).first()
    if not phenotype:
        raise HTTPException(status_code=404, detail="Phenotype not found")
    return phenotype


@router.patch("/{phenotype_id}", response_model=PhenotypeResponse)
def update_phenotype(phenotype_id: int, phenotype_update: PhenotypeUpdate, db: Session = Depends(get_db)):
    phenotype = db.query(Phenotype).filter(Phenotype.id == phenotype_id).first()
    if not phenotype:
        raise HTTPException(status_code=404, detail="Phenotype not found")
    update_data = phenotype_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(phenotype, key, value)
    db.commit()
    db.refresh(phenotype)
    return phenotype


@router.delete("/{phenotype_id}", status_code=204)
def delete_phenotype(phenotype_id: int, db: Session = Depends(get_db)):
    phenotype = db.query(Phenotype).filter(Phenotype.id == phenotype_id).first()
    if not phenotype:
        raise HTTPException(status_code=404, detail="Phenotype not found")
    db.delete(phenotype)
    db.commit()
