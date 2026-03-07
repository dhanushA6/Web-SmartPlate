from fastapi import APIRouter, HTTPException

from ..database import get_users_collection, user_to_public_dict
from ..models.user_model import UserCreate, UserLogin, UserInDB


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(user: UserCreate):
    users = get_users_collection()
    existing = users.find_one({"user_id": user.user_id})
    if existing:
        raise HTTPException(status_code=400, detail="User ID already exists")

    doc = UserInDB(user_id=user.user_id, password=user.password).model_dump()
    users.insert_one(doc)
    return {"success": True}


@router.post("/login")
def login(payload: UserLogin):
    users = get_users_collection()
    doc = users.find_one({"user_id": payload.user_id})
    if not doc or doc.get("password") != payload.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    public = user_to_public_dict(doc)
    return {
        "success": True,
        "user_id": public["user_id"],
        "profile_completed": public.get("profile_completed", False),
    }

