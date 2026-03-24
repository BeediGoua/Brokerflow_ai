"""
Pydantic model for a supporting document.

Each application can have multiple documents (ID proof, income proof, bank
statement, etc.) with metadata indicating whether it has been provided and
its extraction quality.
"""

from pydantic import BaseModel, Field
from typing import Optional


class Document(BaseModel):
    document_id: str = Field(..., description="Unique identifier for the document")
    application_id: str = Field(..., description="The application to which this document belongs")
    document_type: str = Field(..., description="Type of document (id_proof, income_proof, etc.)")
    is_required: bool = Field(..., description="Whether the document is mandatory for the application")
    is_provided: bool = Field(..., description="Whether the applicant provided this document")
    document_quality_score: Optional[float] = Field(None, description="Quality score of the document extraction")
    extracted_text: Optional[str] = Field(None, description="OCR extracted text from the document")
    extraction_confidence: Optional[float] = Field(None, description="Confidence of the OCR extraction (0-1)")

    class Config:
        extra = "ignore"