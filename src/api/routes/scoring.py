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
from src.models.raw_runtime_loader import predict_application_real
from src.agents.note_parser import parse_note
from src.agents.reviewer import review_application, review_application_detailed
from src.agents.summary_writer import write_summary
from src.rules.recommendation import recommend_detailed


router = APIRouter()


@router.post("/score", response_model=PredictionOut, tags=["Scoring"])
def score_application(app: Application) -> PredictionOut:
    """Score an application and return prediction outputs."""
    # Convert Pydantic model to dict for processing
    app_dict = app.dict()
    # Perform risk prediction (runtime aligned with calibrated artifacts)
    pred = predict_application_real(app_dict)
    # Parse free text note
    parsed = parse_note(app_dict.get("free_text_note", ""))
    # For this demo we have no document metadata via API
    documents = []
    alerts = review_application(app_dict, parsed, documents)
    alert_items = review_application_detailed(app_dict, parsed, documents)
    severity_rank = {"none": 0, "low": 1, "medium": 2, "high": 3}
    derived_severity = "none"
    for item in alert_items:
        sev = str(item.get("severity", "low")).lower()
        if sev in severity_rank and severity_rank[sev] > severity_rank[derived_severity]:
            derived_severity = sev

    # Decide recommended action with V2 policy
    decision = recommend_detailed(
        risk_score=pred["risk_score"],
        threshold=pred.get("threshold_used", 0.5),
        completeness=pred["completeness"],
        alerts=alerts,
        alert_severity=derived_severity,
    )
    rec = decision.action
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
        alerts_structured=alert_items,
        recommendation=rec,
        summary=summary,
        decision_reason_codes=decision.reason_codes,
        decision_alert_severity=decision.alert_severity,
        decision_completeness_bucket=decision.completeness_bucket,
        decision_threshold=float(pred.get("threshold_used", 0.5)),
    )