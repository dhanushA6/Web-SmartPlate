from typing import Any, Dict

from pymongo import MongoClient

from .config import get_settings


settings = get_settings()

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGO_URI)
    return _client


def get_db():
    client = get_client()
    return client[settings.MONGO_DB_NAME]


def get_users_collection():
    return get_db()["users"]


def get_profiles_collection():
    return get_db()["profiles"]


def get_nutrition_collection():
    return get_db()["nutrition_predictions"]


def user_to_public_dict(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Strip Mongo-specific fields and sensitive data."""
    if not doc:
        return {}
    doc = dict(doc)
    doc.pop("_id", None)
    return doc

