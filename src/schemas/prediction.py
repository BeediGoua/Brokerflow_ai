"""
Pydantic model for the prediction output.

This model is used to define the response from the `/score` API endpoint.
It includes the continuous risk score, the risk class, top factors,
completeness, detected alerts and a short summary.
"""

from pydantic import BaseModel, Field
from typing import List, Tuple, Optional, Dict, Any


class PredictionOut(BaseModel):
    application_id: str = Field(..., description="Unique identifier of the application scored")
    risk_score: float = Field(..., description="Continuous probability of default between 0 and 1")
    risk_class: str = Field(..., description="Low, Medium or High based on the risk score")
    top_factors: List[Tuple[str, float]] = Field(..., description="List of (feature, contribution) tuples")
    completeness: float = Field(..., description="Completeness score between 0 and 1")
    alerts: List[str] = Field(..., description="List of inconsistencies or missing items detected")
    alerts_structured: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional structured alerts with code/severity/source",
    )
    recommendation: str = Field(..., description="Recommended action for the underwriter")
    summary: str = Field(..., description="Generated summary for the underwriter")
    decision_reason_codes: Optional[List[str]] = Field(
        default=None,
        description="Optional V2 decision reason codes for auditability",
    )
    decision_alert_severity: Optional[str] = Field(
        default=None,
        description="Optional alert severity bucket used by V2 policy (none/low/high)",
    )
    decision_completeness_bucket: Optional[str] = Field(
        default=None,
        description="Optional completeness bucket used by V2 policy (critical/partial/good)",
    )
    decision_threshold: Optional[float] = Field(
        default=None,
        description="Optional operational threshold used by V2 policy",
    )