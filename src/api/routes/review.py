"""
Review endpoint.

This endpoint exposes the reviewer functionality on its own.  It accepts
application data and returns detected alerts without scoring the risk.
"""

from fastapi import APIRouter
from typing import List

from src.schemas.application import Application
from src.agents.note_parser import parse_note
from src.agents.reviewer import review_application


router = APIRouter()


@router.post("/review", response_model=List[str], tags=["Review"])
def review_endpoint(app: Application) -> List[str]:
    """Return a list of alerts for the given application."""
    app_dict = app.dict()
    parsed = parse_note(app_dict.get("free_text_note", ""))
    documents = []
    alerts = review_application(app_dict, parsed, documents)
    return alerts