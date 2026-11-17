from fastapi import APIRouter

from app.api.v1.endpoints import monitors

api_v1_router = APIRouter()
api_v1_router.include_router(monitors.router, prefix="/monitors", tags=["Monitors"])
