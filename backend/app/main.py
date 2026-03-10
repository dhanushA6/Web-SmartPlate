from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .api import auth_routes, profile_routes, nutrition_routes, rag_routes
from .api.routes import recommendation
from .services.rag_service import warmup_assistant_resources


settings = get_settings()

app = FastAPI(title=settings.APP_NAME)


origins = [o.strip() for o in settings.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_warmup() -> None:
    try:
        warmup_assistant_resources()
    except Exception as e:
        print(f"[Startup] Assistant warmup skipped: {e}")


@app.get("/")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}


app.include_router(auth_routes.router)
app.include_router(profile_routes.router)
app.include_router(nutrition_routes.router)
app.include_router(rag_routes.router)

app.include_router(
    recommendation.router,
    prefix="/api",
    tags=["Food Recommendation"],
)

