
# electricity/api/v1/router.py
from fastapi import APIRouter
from .endpoints import tarifliste, spotprices

router = APIRouter()

router.include_router(tarifliste.router)
router.include_router(spotprices.router)
