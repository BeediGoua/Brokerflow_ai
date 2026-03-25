"""
Pydantic model for a loan application.

The Application model defines the fields that our API accepts when scoring a
loan application.  Many fields are optional in order to simplify the demo.
Missing values will be handled by the preprocessing pipeline.
"""

from pydantic import BaseModel, Field
from typing import List, Optional

from src.schemas.document import Document


class Application(BaseModel):
    application_id: str = Field(..., description="Unique identifier for the application")
    customer_id: str = Field(..., description="Unique identifier for the customer")
    snapshot_date: str = Field(..., description="Date when the application snapshot was taken, YYYY-MM-DD")
    age: Optional[int] = Field(None, description="Age of the applicant in years")
    gender: Optional[str] = Field(None, description="Gender of the applicant")
    marital_status: Optional[str] = Field(None, description="Marital status of the applicant")
    employment_status: Optional[str] = Field(None, description="Employment status (employed, self-employed, unemployed)")
    sector: Optional[str] = Field(None, description="Sector of employment")
    years_in_job: Optional[int] = Field(None, description="Number of years in current job")
    monthly_income: Optional[float] = Field(None, description="Monthly income of the applicant")
    income_stability_score: Optional[float] = Field(None, description="Score reflecting stability of income (0-1)")
    existing_debt: Optional[float] = Field(None, description="Total existing debt of the applicant")
    debt_to_income_ratio: Optional[float] = Field(None, description="Precomputed debt-to-income ratio")
    requested_amount: Optional[float] = Field(None, description="Amount requested for the new loan")
    requested_duration_months: Optional[int] = Field(None, description="Duration of the requested loan in months")
    product_type: Optional[str] = Field(None, description="Type of loan product")
    region: Optional[str] = Field(None, description="Region or branch handling the application")
    account_tenure_months: Optional[int] = Field(None, description="Number of months the customer has held an account")
    prior_loans_count: Optional[int] = Field(None, description="Number of prior loans the customer has had")
    prior_late_payments: Optional[int] = Field(None, description="Number of prior late payments across loans")
    has_prior_default: Optional[int] = Field(None, description="Indicator (0/1) whether the customer ever defaulted before")
    days_since_last_loan: Optional[int] = Field(None, description="Days since the last loan was taken")
    declared_purpose: Optional[str] = Field(None, description="Purpose declared by the applicant for the loan")
    free_text_note: Optional[str] = Field("", description="Unstructured note or email accompanying the application")
    documents: Optional[List[Document]] = Field(
        default_factory=list,
        description="Optional supporting documents metadata for reviewer checks",
    )
    # The target flag is optional for inference; it is present for training purposes
    target_risk_flag: Optional[int] = Field(None, description="1 if the applicant eventually defaulted, else 0")

    # ---------------------------------------------------------------------------
    # Additional synthetic proxy fields
    #
    # The synthetic dataset generator produces several derived variables such as
    # monthly_installment, other_monthly_debt_proxy, residual_income_proxy and
    # credit_score_proxy.  These fields are optional in the API schema.  If
    # provided, they will be used directly by the scoring pipeline; if omitted,
    # the pipeline will compute reasonable defaults from other fields (e.g.
    # requested_amount and requested_duration_months).  Exposing them here
    # ensures that precomputed values from our synthetic generator are not
    # silently dropped by Pydantic when parsed.

    monthly_installment: Optional[float] = Field(
        None, description="Monthly instalment amount for the requested loan (proxy for amortised payments)"
    )
    other_monthly_debt_proxy: Optional[float] = Field(
        None, description="Estimated monthly payment for other debt obligations (30% of instalment by default)"
    )
    residual_income_proxy: Optional[float] = Field(
        None, description="Monthly income minus total monthly debt obligations"
    )
    credit_score_proxy: Optional[float] = Field(
        None, description="Synthetic credit score proxy based on late payments, DTI and employment stability"
    )

    class Config:
        extra = "ignore"