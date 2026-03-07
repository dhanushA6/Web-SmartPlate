from dataclasses import dataclass
from typing import Optional, List


@dataclass
class UserProfile:
    hba1c_percent: Optional[float] = None
    fasting_glucose_mg_dl: Optional[float] = None
    post_prandial_glucose_mg_dl: Optional[float] = None
    hypoglycemia_history: Optional[bool] = None
    diabetes_duration_years: Optional[int] = None

    ldl_cholesterol_mg_dl: Optional[float] = None
    hdl_cholesterol_mg_dl: Optional[float] = None
    triglycerides_mg_dl: Optional[float] = None

    systolic_bp_mmHg: Optional[float] = None
    diastolic_bp_mmHg: Optional[float] = None

    eGFR: Optional[float] = None
    creatinine_mg_dl: Optional[float] = None

    bmi: Optional[float] = None

    age_years: Optional[int] = None
    sex: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    activity_level: Optional[str] = None
    dietary_preference: Optional[str] = None
    allergies: Optional[List[str]] = None
    goal: Optional[str] = None


class RiskAnalyzer:
    @staticmethod
    def glycemic_risk(user: UserProfile):
        score = 0
        has_data = False

        if user.hba1c_percent is not None:
            has_data = True
            if user.hba1c_percent >= 8:
                score += 3
            elif user.hba1c_percent >= 7:
                score += 2

        if user.fasting_glucose_mg_dl is not None:
            has_data = True
            if user.fasting_glucose_mg_dl >= 160:
                score += 2
            elif user.fasting_glucose_mg_dl >= 130:
                score += 1

        if user.post_prandial_glucose_mg_dl is not None:
            has_data = True
            if user.post_prandial_glucose_mg_dl >= 250:
                score += 2
            elif user.post_prandial_glucose_mg_dl >= 180:
                score += 1

        if user.diabetes_duration_years is not None:
            has_data = True
            if user.diabetes_duration_years >= 10:
                score += 1

        if user.hypoglycemia_history is not None:
            has_data = True
            if user.hypoglycemia_history:
                score += 1

        if not has_data:
            return "UNKNOWN"

        if score >= 5:
            return "HIGH"
        elif score >= 3:
            return "MODERATE"
        return "LOW"

    @staticmethod
    def lipid_risk(user: UserProfile):
        score = 0
        has_data = False

        if user.ldl_cholesterol_mg_dl is not None:
            has_data = True
            if user.ldl_cholesterol_mg_dl > 160:
                score += 2
            elif user.ldl_cholesterol_mg_dl > 130:
                score += 1

        if user.triglycerides_mg_dl is not None:
            has_data = True
            if user.triglycerides_mg_dl > 200:
                score += 1

        if user.hdl_cholesterol_mg_dl is not None:
            has_data = True
            if user.hdl_cholesterol_mg_dl < 40:
                score += 1

        if not has_data:
            return "UNKNOWN"

        if score >= 3:
            return "HIGH"
        elif score >= 1:
            return "MODERATE"
        return "LOW"

    @staticmethod
    def bp_risk(user: UserProfile):
        if user.systolic_bp_mmHg is None or user.diastolic_bp_mmHg is None:
            return "UNKNOWN"
        sys = user.systolic_bp_mmHg
        dia = user.diastolic_bp_mmHg
        if sys >= 140 or dia >= 90:
            return "STAGE2"
        elif sys >= 130 or dia >= 80:
            return "STAGE1"
        elif sys < 120 and dia < 80:
            return "NORMAL"
        return "ELEVATED"

    @staticmethod
    def kidney_risk(user: UserProfile):
        if user.eGFR is None:
            return "UNKNOWN"
        egfr = user.eGFR
        if egfr >= 90:
            return "NORMAL"
        elif 60 <= egfr < 90:
            return "MILD_IMPAIRMENT"
        elif 30 <= egfr < 60:
            return "MODERATE_IMPAIRMENT"
        return "SEVERE_IMPAIRMENT"

    @staticmethod
    def obesity_risk(user: UserProfile):
        if user.bmi is None:
            return "UNKNOWN"
        bmi = user.bmi
        if bmi >= 30:
            return "HIGH"
        elif bmi >= 25:
            return "MODERATE"
        return "LOW"

    @staticmethod
    def analyze(user: UserProfile):
        return {
            "glycemic_risk": RiskAnalyzer.glycemic_risk(user),
            "lipid_risk": RiskAnalyzer.lipid_risk(user),
            "bp_risk": RiskAnalyzer.bp_risk(user),
            "kidney_risk": RiskAnalyzer.kidney_risk(user),
            "obesity_risk": RiskAnalyzer.obesity_risk(user),
        }

