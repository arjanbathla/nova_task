from datetime import datetime, timezone
from typing import Literal
import uuid

from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator

from app.pricing import calculate_quote

app = FastAPI()


class ApplicationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=18, le=80)
    smoker: bool
    coverage_amount: int = Field(ge=50000, le=1000000)
    occupation: Literal["low_risk", "medium_risk", "high_risk"]
    pre_existing_conditions: bool

    @field_validator("coverage_amount")
    @classmethod
    def coverage_must_be_multiple_of_10000(cls, v: int) -> int:
        if v % 10000 != 0:
            raise ValueError("coverage_amount must be a multiple of 10000")
        return v


class ApplicationResponse(BaseModel):
    application_id: str
    status: str
    quote: float | None
    breakdown: dict
    reason: str | None
    submitted_at: str


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/applications", status_code=201)
def create_application(request: ApplicationRequest) -> ApplicationResponse:
    # Calculate quote using pricing logic
    pricing_result = calculate_quote(
        age=request.age,
        smoker=request.smoker,
        coverage_amount=request.coverage_amount,
        occupation=request.occupation,
        pre_existing_conditions=request.pre_existing_conditions
    )
    
    # Generate application metadata
    application_id = str(uuid.uuid4())
    submitted_at = datetime.now(timezone.utc).isoformat()
    
    # Combine pricing result with metadata
    return ApplicationResponse(
        application_id=application_id,
        status=pricing_result["status"],
        quote=pricing_result["quote"],
        breakdown=pricing_result["breakdown"],
        reason=pricing_result["reason"],
        submitted_at=submitted_at
    )
