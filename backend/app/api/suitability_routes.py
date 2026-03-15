from __future__ import annotations

import os
import tempfile
from typing import Any, Dict, List

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..services.suitability_service import (
  analyze_food_image_from_path,
  evaluate_meal_suitability,
  get_food_nutrition_from_name,
)


router = APIRouter(prefix="/suitability", tags=["suitability"])


@router.post("/detect-foods")
async def detect_foods(file: UploadFile = File(...)) -> Dict[str, Any]:
  """
  Image-based multi-food detection endpoint.
  Wraps dummy.sample.analyze_food_image and returns its JSON output as-is.
  """
  suffix = os.path.splitext(file.filename or "")[1] or ".bin"

  try:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
      contents = await file.read()
      tmp.write(contents)
      tmp_path = tmp.name

    result = analyze_food_image_from_path(tmp_path)
  except Exception as exc:
    raise HTTPException(status_code=500, detail=str(exc)) from exc
  finally:
    if "tmp_path" in locals() and os.path.exists(tmp_path):
      os.remove(tmp_path)

  if isinstance(result, dict) and result.get("error"):
    raise HTTPException(status_code=500, detail=result["error"])

  return result


@router.get("/food-nutrition")
def food_nutrition(food_name: str) -> Dict[str, Any]:
  """
  Retrieve nutrient values per 100 g for a given food name.
  Wraps dummy.nutrition.get_food_nutrition and returns its dict output as-is.
  """
  result = get_food_nutrition_from_name(food_name)
  if not result:
    raise HTTPException(status_code=404, detail="Nutrition data not found")
  if isinstance(result, dict) and result.get("error"):
    raise HTTPException(status_code=500, detail=result["error"])
  return result


@router.post("/check-meal")
def check_meal(payload: Dict[str, Any]) -> Dict[str, Any]:
  """
  Meal-level suitability evaluation endpoint.
  Expects a JSON body containing at minimum:
  - user_id: str
  - meal_type: str (Breakfast, Lunch, Snacks, Dinner)
  - foods: list of { food_name, portion_g, nutrients_per_100g }
  The response is exactly what FoodSuitabilityEngine.evaluate returns.
  """
  user_id = payload.get("user_id")
  meal_type = payload.get("meal_type")
  foods: List[Dict[str, Any]] = payload.get("foods") or []

  if not user_id or not meal_type or not foods:
    raise HTTPException(
      status_code=400,
      detail="user_id, meal_type and at least one food are required",
    )

  try:
    result = evaluate_meal_suitability(
      user_id=user_id,
      meal_type=meal_type,
      foods=foods,
    )
  except ValueError as exc:
    # For example when profile is missing
    raise HTTPException(status_code=404, detail=str(exc)) from exc
  except Exception as exc:
    raise HTTPException(status_code=500, detail=str(exc)) from exc

  return result

