from pathlib import Path
from typing import List, Literal

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...services.food_recommender import FoodRecommender


router = APIRouter()


class RecommendFoodRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    meal_type: Literal["breakfast", "lunch", "snacks", "dinner"]
    veg_only: bool

    target_carbs_g: float
    target_protein_g: float
    target_fiber_g: float
    target_fat_g: float
    target_calories_kcal: float

    hba1c_percent: float
    triglycerides_mg_dl: float
    ldl_cholesterol_mg_dl: float
    systolic_bp_mmHg: float
    diastolic_bp_mmHg: float


class NutritionValues(BaseModel):
    carbs: float
    protein: float
    fiber: float
    fat: float
    calories: float


class RecommendedFood(BaseModel):
    food_id: int
    food_name: str
    quantity_g: float
    unit: str
    nutrition: NutritionValues


class RecommendFoodResponse(BaseModel):
    foods: List[RecommendedFood]


class FoodFeedbackRequest(BaseModel):
    user_id: str
    food_id: int
    action: Literal["like", "dislike", "skip"]


# Load CSV once at startup
BASE_DIR = Path(__file__).resolve().parents[3]  # backend/
DATA_DIR = BASE_DIR / "app" / "data"
FOOD_CSV_PATH = DATA_DIR / "south_indian_food_with_id.csv"

if not FOOD_CSV_PATH.exists():
    raise RuntimeError(f"Food CSV not found at {FOOD_CSV_PATH}")

_food_df = pd.read_csv(FOOD_CSV_PATH)
_recommender = FoodRecommender(_food_df)


@router.post("/recommend-food", response_model=RecommendFoodResponse)
def recommend_food(payload: RecommendFoodRequest) -> RecommendFoodResponse:
    user = {
        "meal_type": payload.meal_type,
        "veg_only": payload.veg_only,
        "target_carbs_g": payload.target_carbs_g,
        "target_protein_g": payload.target_protein_g,
        "target_fiber_g": payload.target_fiber_g,
        "target_fat_g": payload.target_fat_g,
        "target_calories_kcal": payload.target_calories_kcal,
        "hba1c_percent": payload.hba1c_percent,
        "triglycerides_mg_dl": payload.triglycerides_mg_dl,
        "ldl_cholesterol_mg_dl": payload.ldl_cholesterol_mg_dl,
        "systolic_bp_mmHg": payload.systolic_bp_mmHg,
        "diastolic_bp_mmHg": payload.diastolic_bp_mmHg,
    }

    foods = _recommender.recommend(payload.user_id, user)

    if not foods:
        raise HTTPException(
            status_code=404, detail="No suitable foods found for the given criteria."
        )

    # Build response with nutrition values
    response_foods: List[RecommendedFood] = []

    for food_name, qty, unit, food_id in foods:
        row = _food_df[_food_df["food_id"] == food_id]
        if row.empty:
            continue
        row = row.iloc[0]

        factor = qty / 100.0
        nutrition = NutritionValues(
            carbs=float(row["carb_g"] * factor),
            protein=float(row["protein_g"] * factor),
            fiber=float(row["fiber_g"] * factor),
            fat=float(row["fat_g"] * factor),
            calories=float(row["energy_kcal"] * factor),
        )

        response_foods.append(
            RecommendedFood(
                food_id=int(food_id),
                food_name=str(food_name),
                quantity_g=float(qty),
                unit=str(unit),
                nutrition=nutrition,
            )
        )

    return RecommendFoodResponse(foods=response_foods)


@router.post("/food-feedback")
def food_feedback(payload: FoodFeedbackRequest) -> dict:
    _recommender.feedback(payload.user_id, payload.food_id, payload.action)
    return {"success": True}

