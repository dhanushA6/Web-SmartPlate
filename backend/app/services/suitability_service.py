from __future__ import annotations

from typing import Any, Dict, List

from ..database import get_profiles_collection
from .nutrition_predictor import predict_nutrition_from_profile
from .. import imageproccessor as image_processor  # type: ignore
from .. import nutritionquery as nutrition_query  # type: ignore
from .. import suitabilitycheck as suitability_engine  # type: ignore


def _coerce_float(value: Any) -> float | None:
  try:
    if value is None:
      return None
    return float(value)
  except (TypeError, ValueError):
    return None


def _normalise_nutrients_payload(
  item: Dict[str, Any],
  portion_g: float,
) -> Dict[str, Any]:
  """
  Accepts nutrient payloads from multiple frontend shapes and returns only
  valid FoodNutrients fields.

  Supported input shapes:
  - item["nutrients_per_100g"]
  - item["nutrition_per_100g"]
  - item["macro_totals"] (portion totals, back-converted to per-100 g)
  """
  allowed = set(suitability_engine.FoodNutrients.__dataclass_fields__.keys())

  raw: Dict[str, Any] = {}
  if isinstance(item.get("nutrients_per_100g"), dict):
    raw = dict(item["nutrients_per_100g"])
  elif isinstance(item.get("nutrition_per_100g"), dict):
    raw = dict(item["nutrition_per_100g"])

  # If caller passed macro totals for the selected portion, convert to per-100 g.
  if not raw and isinstance(item.get("macro_totals"), dict):
    totals = item["macro_totals"]
    factor = (100.0 / portion_g) if portion_g > 0 else 0.0
    raw = {
      "energy_kcal": _coerce_float(totals.get("energy_kcal")),
      "carb_g": _coerce_float(totals.get("carb_g")),
      "protein_g": _coerce_float(totals.get("protein_g")),
      "fat_g": _coerce_float(totals.get("fat_g")),
      "fibre_g": _coerce_float(totals.get("fibre_g") or totals.get("fiber_g")),
      "freesugar_g": _coerce_float(totals.get("freesugar_g")),
      "sodium_mg": _coerce_float(totals.get("sodium_mg")),
      "potassium_mg": _coerce_float(totals.get("potassium_mg")),
      "sfa_mg": _coerce_float(totals.get("sfa_mg")),
      "cholesterol_mg": _coerce_float(totals.get("cholesterol_mg")),
    }
    for k, v in list(raw.items()):
      raw[k] = round(v * factor, 6) if v is not None else None

  # Common alias handling from manual/frontend payloads.
  if "fiber_g" in raw and "fibre_g" not in raw:
    raw["fibre_g"] = raw.get("fiber_g")
  if "carbs" in raw and "carb_g" not in raw:
    raw["carb_g"] = raw.get("carbs")
  if "calories" in raw and "energy_kcal" not in raw:
    raw["energy_kcal"] = raw.get("calories")

  # Keep only dataclass-supported nutrient fields and numeric-coerce values.
  cleaned: Dict[str, Any] = {}
  for key, value in raw.items():
    if key in allowed:
      num = _coerce_float(value)
      cleaned[key] = num

  return cleaned


def analyze_food_image_from_path(image_path: str) -> Dict[str, Any]:
  """
  Thin wrapper over dummy.sample.analyze_food_image.
  Returns the model JSON as-is so the frontend can use the same schema.
  """
  return image_processor.analyze_food_image(image_path)


def get_food_nutrition_from_name(food_name: str) -> Dict[str, Any]:
  """
  Thin wrapper over dummy.nutrition.get_food_nutrition.
  """
  return nutrition_query.get_food_nutrition(food_name)


def _build_patient_profile(doc: Dict[str, Any]) -> suitability_engine.PatientProfile:
  """
  Map the stored profile document into the PatientProfile dataclass
  expected by the rule engine. Where fields are missing, use safe defaults.
  """
  # Basic demographics
  age = int(doc.get("age") or 50)
  gender = doc.get("gender") or "Male"
  height_cm = float(doc.get("height_cm") or 170.0)
  weight_kg = float(doc.get("weight_kg") or 70.0)
  bmi = float(doc.get("bmi") or (weight_kg / ((height_cm / 100) ** 2)))

  if bmi < 18.5:
    bmi_class_label = "Underweight"
  elif bmi < 25:
    bmi_class_label = "Normal"
  elif bmi < 30:
    bmi_class_label = "Overweight"
  else:
    bmi_class_label = "Obese"

  # Activity level
  pal_raw = (doc.get("physical_activity_level") or "sedentary").strip().lower()
  pal_map = {
    "sedentary": suitability_engine.PhysicalActivityLevel.SEDENTARY,
    "light": suitability_engine.PhysicalActivityLevel.LIGHT,
    "moderate": suitability_engine.PhysicalActivityLevel.MODERATE,
    "active": suitability_engine.PhysicalActivityLevel.ACTIVE,
    "very_active": suitability_engine.PhysicalActivityLevel.VERY_ACTIVE,
  }
  physical_activity_level = pal_map.get(
    pal_raw, suitability_engine.PhysicalActivityLevel.SEDENTARY
  )

  steps_per_day = int(doc.get("steps_per_day") or 4000)
  sleep_hours = float(doc.get("sleep_hours") or 7.0)

  # Glycaemic status
  diabetes_duration_years = int(doc.get("diabetes_duration_years") or 5)
  hba1c_percent = float(doc.get("hba1c_percent") or 7.5)
  fasting_glucose_mg_dl = float(doc.get("fasting_glucose_mg_dl") or 120.0)
  postprandial_glucose_mg_dl = float(doc.get("postprandial_glucose_mg_dl") or 180.0)

  # Lipids
  triglycerides_mg_dl = float(doc.get("triglycerides_mg_dl") or 150.0)
  ldl_cholesterol_mg_dl = float(doc.get("ldl_cholesterol_mg_dl") or 120.0)
  hdl_cholesterol_mg_dl = float(doc.get("hdl_cholesterol_mg_dl") or 40.0)

  # Blood pressure (note different field casing in Profile vs engine)
  systolic_bp = float(
    doc.get("systolic_bp_mmHg") or doc.get("systolic_bp_mmhg") or 130.0
  )
  diastolic_bp = float(
    doc.get("diastolic_bp_mmHg") or doc.get("diastolic_bp_mmhg") or 80.0
  )

  # Renal function → derive CKD stage from eGFR when possible
  egfr = float(doc.get("egfr_ml_min_1_73m2") or 90.0)
  if egfr >= 90:
    ckd_stage = suitability_engine.CKDStage.G1
  elif egfr >= 60:
    ckd_stage = suitability_engine.CKDStage.G2
  elif egfr >= 30:
    ckd_stage = suitability_engine.CKDStage.G3
  elif egfr >= 15:
    ckd_stage = suitability_engine.CKDStage.G4
  else:
    ckd_stage = suitability_engine.CKDStage.G5

  smoking_status = int(doc.get("smoking_status") or 0)
  alcohol_use = int(doc.get("alcohol_use") or 0)

  # Primary goal
  goal_raw = (doc.get("primary_goal") or "glycemic_control").strip().lower()
  if "weight" in goal_raw:
    primary_goal = suitability_engine.PrimaryGoal.WEIGHT_LOSS
  elif "maint" in goal_raw:
    primary_goal = suitability_engine.PrimaryGoal.MAINTENANCE
  else:
    primary_goal = suitability_engine.PrimaryGoal.GLYCEMIC_CONTROL

  return suitability_engine.PatientProfile(
    age=age,
    gender=gender,
    height_cm=height_cm,
    weight_kg=weight_kg,
    bmi=bmi,
    bmi_class_label=bmi_class_label,
    physical_activity_level=physical_activity_level,
    steps_per_day=steps_per_day,
    sleep_hours=sleep_hours,
    diabetes_duration_years=diabetes_duration_years,
    hba1c_percent=hba1c_percent,
    fasting_glucose_mg_dl=fasting_glucose_mg_dl,
    postprandial_glucose_mg_dl=postprandial_glucose_mg_dl,
    triglycerides_mg_dl=triglycerides_mg_dl,
    ldl_cholesterol_mg_dl=ldl_cholesterol_mg_dl,
    hdl_cholesterol_mg_dl=hdl_cholesterol_mg_dl,
    systolic_bp_mmhg=systolic_bp,
    diastolic_bp_mmhg=diastolic_bp,
    egfr_ml_min_1_73m2=egfr,
    ckd_stage_label=ckd_stage,
    smoking_status=smoking_status,
    alcohol_use=alcohol_use,
    primary_goal=primary_goal,
  )


def _build_meal_targets(profile_doc: Dict[str, Any], meal_type: str) -> suitability_engine.MealMacroTargets:
  """
  Use the existing LightGBM model via nutrition_predictor to obtain
  per-meal macro targets, then map them into MealMacroTargets.
  """
  nutrition = predict_nutrition_from_profile(profile_doc)
  meal_key = meal_type.strip().lower()
  # Normalise UI labels to keys used in nutrition_predictor
  if meal_key == "breakfast":
    split_key = "breakfast"
  elif meal_key == "lunch":
    split_key = "lunch"
  elif meal_key == "snacks":
    split_key = "snacks"
  elif meal_key == "dinner":
    split_key = "dinner"
  else:
    split_key = "lunch"

  splits = nutrition["meal_splits"][split_key]

  return suitability_engine.MealMacroTargets(
    calories_kcal=float(splits["daily_calories_kcal"]),
    carbohydrates_g=float(splits["daily_carbohydrates_g"]),
    protein_g=float(splits["daily_protein_g"]),
    fat_g=float(splits["daily_fat_g"]),
    fiber_g=float(splits["daily_fiber_g"]),
  )


def evaluate_meal_suitability(
  user_id: str,
  meal_type: str,
  foods: List[Dict[str, Any]],
) -> Dict[str, Any]:
  """
  High-level suitability evaluation entry point:
  - fetch user profile
  - build PatientProfile + MealMacroTargets
  - map incoming foods into FoodItem list
  - call FoodSuitabilityEngine.evaluate and return its JSON result as-is.
  """
  profiles = get_profiles_collection()
  doc = profiles.find_one({"user_id": user_id})
  if not doc:
    raise ValueError("Profile not found for user")

  # Strip Mongo metadata
  doc = dict(doc)
  doc.pop("_id", None)

  patient = _build_patient_profile(doc)
  meal_targets = _build_meal_targets(doc, meal_type)

  food_items: List[suitability_engine.FoodItem] = []
  for item in foods:
    portion_g = float(item.get("portion_g") or 0.0)
    nutrients_raw = _normalise_nutrients_payload(item, portion_g)
    nutrients = suitability_engine.FoodNutrients(**nutrients_raw)
    food_items.append(
      suitability_engine.FoodItem(
        food_name=item.get("food_name") or "",
        portion_g=portion_g,
        nutrients_per_100g=nutrients,
      )
    )

  engine = suitability_engine.FoodSuitabilityEngine(patient, meal_targets)
  result = engine.evaluate(food_items)
  return result

