# llm/api/endpoints.py
from fastapi import APIRouter
from .health import router as health_router
from .ask import router as ask_router
from .provider import router as provider_router
from .status import router as status_router
from .detect import router as detect_router  # new

router = APIRouter()

router.include_router(health_router)
router.include_router(ask_router)
router.include_router(provider_router)
router.include_router(status_router)
router.include_router(detect_router)  # add