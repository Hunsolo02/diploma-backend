from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.face_feature import FaceFeature
from schemas.face_feature import FaceFeatureCreate, FaceFeatureUpdate, FaceFeatureResponse

router = APIRouter(prefix="/face-features", tags=["face-features"])


@router.get("/", response_model=list[FaceFeatureResponse])
def list_face_features(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    face_features = db.query(FaceFeature).offset(skip).limit(limit).all()
    return face_features


@router.post("/", response_model=FaceFeatureResponse)
def create_face_feature(face_feature: FaceFeatureCreate, db: Session = Depends(get_db)):
    db_face_feature = FaceFeature(**face_feature.model_dump())
    db.add(db_face_feature)
    db.commit()
    db.refresh(db_face_feature)
    return db_face_feature


@router.get("/{face_feature_id}", response_model=FaceFeatureResponse)
def get_face_feature(face_feature_id: int, db: Session = Depends(get_db)):
    face_feature = db.query(FaceFeature).filter(FaceFeature.id == face_feature_id).first()
    if not face_feature:
        raise HTTPException(status_code=404, detail="Face feature not found")
    return face_feature


@router.patch("/{face_feature_id}", response_model=FaceFeatureResponse)
def update_face_feature(face_feature_id: int, face_feature_update: FaceFeatureUpdate, db: Session = Depends(get_db)):
    face_feature = db.query(FaceFeature).filter(FaceFeature.id == face_feature_id).first()
    if not face_feature:
        raise HTTPException(status_code=404, detail="Face feature not found")
    update_data = face_feature_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(face_feature, key, value)
    db.commit()
    db.refresh(face_feature)
    return face_feature


@router.delete("/{face_feature_id}", status_code=204)
def delete_face_feature(face_feature_id: int, db: Session = Depends(get_db)):
    face_feature = db.query(FaceFeature).filter(FaceFeature.id == face_feature_id).first()
    if not face_feature:
        raise HTTPException(status_code=404, detail="Face feature not found")
    db.delete(face_feature)
    db.commit()
