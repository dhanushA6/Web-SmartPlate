import os
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"


if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


class Settings:
    """Application configuration loaded from backend/.env."""

    # Core
    APP_NAME: str = "Diabetes Nutrition & AI Diet Assistant"
    BACKEND_CORS_ORIGINS: str = os.getenv(
        "BACKEND_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )

    # MongoDB
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "diabetes_nutrition_db")

    # Google / Gemini / OCR
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
    GCP_LOCATION: str = os.getenv("GCP_LOCATION", "")
    GCP_PROCESSOR_ID: str = os.getenv("GCP_PROCESSOR_ID", "")
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS", ""
    )

    # RAG / Chroma
    NALAM_DB_PATH: str = os.getenv("NALAM_DB_PATH", "./nalam_chroma_db")
    NALAM_COLLECTION_NAME: str = os.getenv(
        "NALAM_COLLECTION_NAME", "nalam_knowledge"
    )

    # ML model paths
    NUTRITION_MODEL_PATH: str = os.getenv(
        "NUTRITION_MODEL_PATH",
        str(BASE_DIR / "app" / "ml_models" / "LightGBM_pipeline.pkl"),
    )


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()

    # Ensure Google credentials are visible to Document AI
    if settings.GOOGLE_APPLICATION_CREDENTIALS:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
            settings.GOOGLE_APPLICATION_CREDENTIALS
        )

    return settings

