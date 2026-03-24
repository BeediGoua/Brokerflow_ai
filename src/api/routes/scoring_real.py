"""Real-runtime scoring endpoint.

This v2 route uses calibrated artifacts trained on the raw Zindi flow while
preserving the same response contract as v1 for easy client migration.
"""

from fastapi import APIRouter

from src.schemas.application import Application
from src.schemas.prediction import PredictionOut
from src.models.raw_runtime_loader import predict_application_real
from src.agents.note_parser import parse_note
from src.agents.reviewer import review_application
from src.agents.summary_writer import write_summary
from src.rules.recommendation import recommend


router = APIRouter()


@router.post("/score", response_model=PredictionOut, tags=["Scoring Real Runtime"])
def score_application_real_runtime(app: Application) -> PredictionOut:
    """Score an application using the calibrated raw-runtime model."""
    app_dict = app.dict()

    pred = predict_application_real(app_dict)
    parsed = parse_note(app_dict.get("free_text_note", ""))
    documents = []
    alerts = review_application(app_dict, parsed, documents)
    rec = recommend(pred["risk_class"], pred["completeness"], alerts)

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
