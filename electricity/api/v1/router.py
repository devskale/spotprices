
# electricity/api/v1/router.py
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from config import get_secret
from .endpoints import tarifliste, spotprices


def require_bearer_auth(authorization: Optional[str] = Header(default=None)) -> None:
    expected = get_secret("strom_tarif_api_key", "")
    if not expected:
        return

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    if token != expected:
        raise HTTPException(status_code=403, detail="Invalid bearer token")


router = APIRouter()

router.include_router(tarifliste.router, dependencies=[Depends(require_bearer_auth)])
router.include_router(spotprices.router, dependencies=[Depends(require_bearer_auth)])
