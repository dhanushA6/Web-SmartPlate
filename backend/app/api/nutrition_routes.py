from fastapi import APIRouter, HTTPException

from ..database import get_profiles_collection
from ..services.nutrition_predictor import predict_nutrition_from_profile


router = APIRouter(prefix="/nutrition", tags=["nutrition"])


@router.post("/predict-nutrition")
def predict_nutrition(user_id: str):
    profiles = get_profiles_collection()
    doc = profiles.find_one({"user_id": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Profile not found")

    doc.pop("_id", None)

    nutrition = predict_nutrition_from_profile(doc)

    return {
        "user_id": user_id,
        "daily": nutrition["daily"],
        "distribution": nutrition["distribution"],
        "meal_splits": nutrition["meal_splits"],
    }

