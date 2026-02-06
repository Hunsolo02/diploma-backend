from models.item import Item
from models.user import User
from models.region import Region
from models.phenotype import Phenotype
from models.face_feature import FaceFeature
from models.user_profile import UserProfile
from models.user_profile_face_feature import user_profile_face_features  # noqa: F401 - register table

__all__ = ["Item", "User", "Region", "Phenotype", "FaceFeature", "UserProfile"]
