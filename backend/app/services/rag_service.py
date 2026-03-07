from typing import Any, Dict, Optional

from ..config import get_settings
from ..database import get_profiles_collection
from ..models.profile_model import Profile
from ..services.nutrition_predictor import predict_nutrition_from_profile
from ..rag.nalam_retriever import NalamRetriever
from ..rag.nalam_generator import NalamGenerator
from ..rag.nalam_risk_engine import RiskAnalyzer, UserProfile
from ..rag.food_recommendations import mock_food_recommendation


settings = get_settings()

_retriever: Optional[NalamRetriever] = None
_generator: Optional[NalamGenerator] = None


def init_rag():
    global _retriever, _generator
    if _retriever is None:
        _retriever = NalamRetriever(
            db_path=settings.NALAM_DB_PATH,
            collection_name=settings.NALAM_COLLECTION_NAME,
        )
    if _generator is None:
        _generator = NalamGenerator(api_key=settings.GEMINI_API_KEY)


def warmup_assistant_resources() -> None:
    """
    Eagerly initialize assistant dependencies during app startup so
    the first user question does not pay model/vector-store cold-start latency.
    """
    init_rag()
    assert _retriever is not None

    try:
        # Prime embedding + vector query path once to avoid first-request delay.
        _retriever.get_relevant_context("diabetes nutrition guidance", top_k=1)
        print("[Startup] Assistant RAG resources are warmed up.")
    except Exception as e:
        print(f"[Startup] Assistant RAG warmup completed with warning: {e}")


def _compact_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _has_any_medical_data(medical_dict: Dict[str, Any]) -> bool:
    return bool(medical_dict)


def _load_profile(user_id: str) -> Dict[str, Any]:
    profiles = get_profiles_collection()
    doc = profiles.find_one({"user_id": user_id})
    if not doc:
        raise ValueError("Profile not found for user.")
    doc.pop("_id", None)
    return doc


def _build_risk_profile(profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    medical_mapping = {
        "hba1c_percent": profile_data.get("hba1c_percent"),
        "fasting_glucose_mg_dl": profile_data.get("fasting_glucose_mg_dl"),
        "post_prandial_glucose_mg_dl": profile_data.get("postprandial_glucose_mg_dl"),
        "diabetes_duration_years": profile_data.get("diabetes_duration_years"),
        "ldl_cholesterol_mg_dl": profile_data.get("ldl_cholesterol_mg_dl"),
        "hdl_cholesterol_mg_dl": profile_data.get("hdl_cholesterol_mg_dl"),
        "triglycerides_mg_dl": profile_data.get("triglycerides_mg_dl"),
        "systolic_bp_mmHg": profile_data.get("systolic_bp_mmHg"),
        "diastolic_bp_mmHg": profile_data.get("diastolic_bp_mmHg"),
        "eGFR": profile_data.get("egfr_ml_min_1_73m2"),
        "bmi": profile_data.get("bmi"),
    }

    if not _has_any_medical_data(_compact_dict(medical_mapping)):
        return None

    user_profile = UserProfile(**medical_mapping)  # type: ignore[arg-type]
    return RiskAnalyzer.analyze(user_profile)


def build_structured_context(
    user_id: str,
) -> Dict[str, Any]:
    profile_data = _load_profile(user_id)
    profile_model = Profile(**profile_data)

    medical_dict = _compact_dict(
        {
            "age": profile_model.age,
            "gender": profile_model.gender,
            "height_cm": profile_model.height_cm,
            "weight_kg": profile_model.weight_kg,
            "bmi": profile_model.bmi,
            "diabetes_duration_years": profile_model.diabetes_duration_years,
            "hba1c_percent": profile_model.hba1c_percent,
            "fasting_glucose_mg_dl": profile_model.fasting_glucose_mg_dl,
            "postprandial_glucose_mg_dl": profile_model.postprandial_glucose_mg_dl,
            "triglycerides_mg_dl": profile_model.triglycerides_mg_dl,
            "ldl_cholesterol_mg_dl": profile_model.ldl_cholesterol_mg_dl,
            "hdl_cholesterol_mg_dl": profile_model.hdl_cholesterol_mg_dl,
            "systolic_bp_mmHg": profile_model.systolic_bp_mmHg,
            "diastolic_bp_mmHg": profile_model.diastolic_bp_mmHg,
            "egfr_ml_min_1_73m2": profile_model.egfr_ml_min_1_73m2,
        }
    )

    lifestyle_dict = _compact_dict(
        {
            "physical_activity_level": profile_model.physical_activity_level,
            "steps_per_day": profile_model.steps_per_day,
            "sleep_hours": profile_model.sleep_hours,
            "smoking_status": profile_model.smoking_status,
            "alcohol_use": profile_model.alcohol_use,
            "primary_goal": profile_model.primary_goal,
            "dietary_preference": profile_model.dietary_preference,
        }
    )

    nutrition_targets = predict_nutrition_from_profile(
        profile_model.model_dump(exclude={"user_id"})
    )

    risk_profile = _build_risk_profile(profile_data)

    return {
        "profile": {
            "medical": medical_dict,
            "lifestyle": lifestyle_dict,
        },
        "nutrition": nutrition_targets,
        "risk_analysis": risk_profile,
    }


def ask_assistant(
    user_id: str,
    question: str,
    mode: str = "normal",
    meal_type: Optional[str] = None,
) -> Dict[str, Any]:
    init_rag()
    assert _retriever is not None
    assert _generator is not None

    mode = (mode or "normal").strip().lower()

    structured = build_structured_context(user_id)
    nutrition = structured["nutrition"]
    risk_profile = structured["risk_analysis"]

    if mode == "food_recommendation":
        if not meal_type:
            raise ValueError("meal_type is required when mode='food_recommendation'")

        meal_type_norm = meal_type.strip().lower()
        if meal_type_norm not in nutrition["distribution"]:
            raise ValueError(
                f"Invalid meal_type '{meal_type}'. "
                f"Must be one of: {list(nutrition['distribution'].keys())}"
            )

        meal_macro = nutrition["meal_splits"][meal_type_norm]
        food_rec = mock_food_recommendation(meal_type_norm)

        structured_context = {
            "mode": mode,
            "user_profile": structured["profile"],
            "macro_targets": nutrition,
            "meal_macro": meal_macro,
            "food_recommendation": food_rec,
        }

        answer = _generator.generate_response(
            context="",
            user_question=question,
            risk_profile=risk_profile,
            structured_context=structured_context,
        )

        return {
            "mode": mode,
            "meal_type": meal_type_norm,
            "answer": answer,
            "macro_targets": nutrition,
            "meal_macro": meal_macro,
            "food_recommendation": food_rec,
            "risk_analysis": risk_profile,
        }

    retrieved_context = _retriever.get_relevant_context(question)

    structured_context = {
        "mode": mode,
        "user_profile": structured["profile"],
        "risk_analysis": risk_profile,
        "macro_targets": nutrition,
    }

    answer = _generator.generate_response(
        context=retrieved_context,
        user_question=question,
        risk_profile=risk_profile,
        structured_context=structured_context,
    )

    return {
        "mode": mode,
        "answer": answer,
        "risk_analysis": risk_profile,
        "macro_targets": nutrition,
        "retrieved_context_preview": (
            retrieved_context[:200] + "..." if retrieved_context else "None"
        ),
    }

