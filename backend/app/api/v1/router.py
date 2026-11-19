from fastapi import APIRouter

from app.api.v1.endpoints import auth, incidents, monitors, users

api_v1_router = APIRouter()
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(users.router, prefix="/users", tags=["Users"])
api_v1_router.include_router(monitors.router, prefix="/monitors", tags=["Monitors"])
api_v1_router.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
