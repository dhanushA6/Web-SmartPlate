from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from ..services.rag_service import ask_assistant


router = APIRouter(tags=["assistant"])


class AssistantRequest(BaseModel):
    user_id: str
    message: str
    mode: str = "normal"  # "normal" | "food_recommendation"
    meal_type: str | None = None


@router.post("/ask-assistant")
def ask_assistant_route(payload: AssistantRequest):
    try:
        result = ask_assistant(
            user_id=payload.user_id,
            question=payload.message,
            mode=payload.mode,
            meal_type=payload.meal_type,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

