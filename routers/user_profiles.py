import base64
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.user_profile import UserProfile
from schemas.user_profile import (
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
    profile_to_response,
)

router = APIRouter(prefix="/user-profiles", tags=["user-profiles"])


def _decode_base64(value: str | None) -> bytes | None:
    if not value:
        return None
    try:
        return base64.b64decode(value)
    except Exception:
        return None


@router.get("/", response_model=list[UserProfileResponse])
def list_user_profiles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    profiles = db.query(UserProfile).offset(skip).limit(limit).all()
    return [profile_to_response(p) for p in profiles]


@router.post("/", response_model=UserProfileResponse)
def create_user_profile(profile: UserProfileCreate, db: Session = Depends(get_db)):
    from models.face_feature import FaceFeature

    db_profile = UserProfile(
        region_id=profile.region_id,
        phenotype_analyze=profile.phenotype_analyze,
        original_image=_decode_base64(profile.original_image_base64),
        analyzed_image=_decode_base64(profile.analyzed_image_base64),
    )
    db.add(db_profile)
    db.flush()  # get db_profile.id before setting face_features
    if profile.face_feature_ids:
        face_features = db.query(FaceFeature).filter(FaceFeature.id.in_(profile.face_feature_ids)).all()
        db_profile.face_features = face_features
    db.commit()
    db.refresh(db_profile)
    return profile_to_response(db_profile)


@router.get("/{profile_id}", response_model=UserProfileResponse)
def get_user_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return profile_to_response(profile)


@router.patch("/{profile_id}", response_model=UserProfileResponse)
def update_user_profile(profile_id: int, profile_update: UserProfileUpdate, db: Session = Depends(get_db)):
    from models.face_feature import FaceFeature

    profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    update_data = profile_update.model_dump(exclude_unset=True)
    face_feature_ids = update_data.pop("face_feature_ids", None)
    for key, value in update_data.items():
        if key in ("original_image_base64", "analyzed_image_base64"):
            setattr(profile, key.replace("_base64", ""), _decode_base64(value))
        else:
            setattr(profile, key, value)
    if face_feature_ids is not None:
        face_features = db.query(FaceFeature).filter(FaceFeature.id.in_(face_feature_ids)).all()
        profile.face_features = face_features
    db.commit()
    db.refresh(profile)
    return profile_to_response(profile)


@router.delete("/{profile_id}", status_code=204)
def delete_user_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    db.delete(profile)
    db.commit()
