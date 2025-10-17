"""
API endpoints package for Nutrition LLM application.
"""

from .health import router as health_router
from .ask import router as ask_router
from .provider import router as provider_router
from .status import router as status_router
from .detect import router as detect_router

__all__ = [
    "health_router",
    "ask_router", 
    "provider_router",
    "status_router",
    "detect_router",
]