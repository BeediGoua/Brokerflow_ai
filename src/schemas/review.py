"""
Pydantic model for a human or agent review entry.

This model is not currently used by the API but illustrates how a
review might be stored in a database after the underwriter finalises
the decision.
"""

from pydantic import BaseModel, Field
from typing import Optional


class Review(BaseModel):
    review_id: str = Field(..., description="Unique identifier for the review entry")
    application_id: str = Field(..., description="The application being reviewed")
    predicted_score: float = Field(..., description="Model predicted probability of default")
    predicted_class: str = Field(..., description="Model predicted class (Low/Medium/High)")
    recommended_action: str = Field(..., description="Model recommended action")
    human_decision: Optional[str] = Field(None, description="Actual decision taken by the human reviewer")
    human_risk_class: Optional[str] = Field(None, description="Risk class assigned by the human reviewer")
    reviewer_comment: Optional[str] = Field(None, description="Free‑text comment from the reviewer")
    review_time_seconds: Optional[float] = Field(None, description="Time taken to review in seconds")

    class Config:
        extra = "ignore"


class ReviewAlert(BaseModel):
    code: str = Field(..., description="Stable alert code for decisioning/audit")
    severity: str = Field(..., description="Alert severity bucket (low/medium/high)")
    message: str = Field(..., description="Human-readable alert message")
    source: str = Field(..., description="Detection source (documents/note_parser/cross_check)")
    confidence: float = Field(..., description="Confidence score for the detected alert")

    class Config:
        extra = "ignore"