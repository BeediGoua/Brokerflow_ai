"""
Scoring endpoint.

Exposes a POST endpoint that accepts an application JSON payload and
returns the risk score, class, top factors, completeness, alerts,
recommendation and summary.  Documents are not currently accepted via
API but can be integrated by expanding the request model.
"""

from fastapi import APIRouter

from src.schemas.application import Application
from src.schemas.prediction import PredictionOut
from src.models.predict import predict_application
from src.agents.note_parser import parse_note
from src.agents.reviewer import review_application
from src.agents.summary_writer import write_summary
from src.rules.recommendation import recommend


router = APIRouter()


@router.post("/score", response_model=PredictionOut, tags=["Scoring"])
def score_application(app: Application) -> PredictionOut:
    """Score an application and return prediction outputs."""
    # Convert Pydantic model to dict for processing
    app_dict = app.dict()
    # Perform risk prediction
    pred = predict_application(app_dict)
    # Parse free text note
    parsed = parse_note(app_dict.get("free_text_note", ""))
    # For this demo we have no document metadata via API
    documents = []
    alerts = review_application(app_dict, parsed, documents)
    # Decide recommended action
    rec = recommend(pred["risk_class"], pred["completeness"], alerts)
    # Generate summary
    summary = write_summary(
        risk_class=pred["risk_class"],
        risk_score=pred["risk_score"],
        top_factors=pred["top_factors"],
        recommendation=rec,
        alerts=alerts,
    )
    return PredictionOut(
        application_id=app.application_id,
        risk_score=pred["risk_score"],
        risk_class=pred["risk_class"],
        top_factors=pred["top_factors"],
        completeness=pred["completeness"],
        alerts=alerts,
        recommendation=rec,
        summary=summary,
    )