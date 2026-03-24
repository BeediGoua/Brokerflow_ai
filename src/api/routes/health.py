"""
Health check endpoint.

This endpoint can be used by orchestration systems or load balancers to
determine if the application is up and running.
"""

from fastapi import APIRouter


router = APIRouter()


@router.get("/health", tags=["Health"])
def health() -> dict:
    """Return OK status."""
    return {"status": "ok"}