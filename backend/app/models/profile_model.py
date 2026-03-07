from typing import Optional

from pydantic import BaseModel


class Profile(BaseModel):
    user_id: str

    age: Optional[float] = None
    gender: Optional[str] = None

    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    bmi: Optional[float] = None

    physical_activity_level: Optional[str] = None
    steps_per_day: Optional[float] = None
    sleep_hours: Optional[float] = None

    diabetes_duration_years: Optional[float] = None

    hba1c_percent: Optional[float] = None
    fasting_glucose_mg_dl: Optional[float] = None
    postprandial_glucose_mg_dl: Optional[float] = None

    triglycerides_mg_dl: Optional[float] = None
    ldl_cholesterol_mg_dl: Optional[float] = None
    hdl_cholesterol_mg_dl: Optional[float] = None

    systolic_bp_mmHg: Optional[float] = None
    diastolic_bp_mmHg: Optional[float] = None

    egfr_ml_min_1_73m2: Optional[float] = None

    smoking_status: Optional[int] = 0
    alcohol_use: Optional[int] = 0

    primary_goal: Optional[str] = None
    dietary_preference: Optional[str] = None

