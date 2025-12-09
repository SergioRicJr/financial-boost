"""API module - FastAPI routes and endpoints."""

from app.api.routes import router
from app.api.dependencies import get_current_user

__all__ = [
    "router",
    "get_current_user",
]
