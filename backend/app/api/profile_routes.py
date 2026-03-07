import os
import tempfile
from typing import Dict, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from ..database import (
    get_profiles_collection,
    get_users_collection,
    user_to_public_dict,
)
from ..models.profile_model import Profile
from ..services.medical_report_parser import parse_medical_report


router = APIRouter(prefix="/profile", tags=["profile"])


SUPPORTED_UPLOAD_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/bmp"
}


def _is_supported_upload(content_type: str | None) -> bool:
    if not content_type:
        return False
    return content_type in SUPPORTED_UPLOAD_MIME_TYPES or content_type.startswith(
        "image/"
    )


@router.get("/{user_id}")
def get_profile(user_id: str):
    profiles = get_profiles_collection()
    doc = profiles.find_one({"user_id": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Profile not found")
    return user_to_public_dict(doc)


@router.post("/update")
def update_profile(profile: Profile):
    profiles = get_profiles_collection()
    users = get_users_collection()

    profiles.update_one(
        {"user_id": profile.user_id},
        {"$set": profile.model_dump()},
        upsert=True,
    )

    users.update_one(
        {"user_id": profile.user_id},
        {"$set": {"profile_completed": True}},
    )

    return {"success": True}


@router.post("/upload-medical-report")
async def upload_medical_report(
    user_id: str = Form(...),
    file: UploadFile = File(...),
):
    if not _is_supported_upload(file.content_type):
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. Upload PDF, image, TXT, DOC, or DOCX."
            ),
        )

    try:
        suffix = Path(file.filename or "").suffix or ".bin"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        extracted: Dict[str, Any] = parse_medical_report(
            tmp_path, content_type=file.content_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if "tmp_path" in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)

    return {
        "user_id": user_id,
        "extracted_fields": extracted,
    }

