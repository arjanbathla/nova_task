from datetime import datetime, timezone
from typing import Literal, Annotated, Optional
import uuid
import json

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator, model_validator

from app.pricing import calculate_quote
from app.db import get_engine, init_db, get_session, save_application, get_application_by_id

# Initialize database
engine = get_engine("sqlite:///./insurance.db")
init_db(engine)

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def read_root():
    """Serve the main HTML page."""
    return FileResponse("static/index.html")


def get_db_engine():
    """Dependency to get database engine (can be overridden in tests)."""
    return engine


class ApplicationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=18, le=80)
    smoker: bool
    coverage_amount: int = Field(ge=50000, le=1000000)
    occupation: Literal["low_risk", "medium_risk", "high_risk"]
    pre_existing_conditions: bool
    medical_details: Optional[str] = Field(None, max_length=1000)

    @field_validator("coverage_amount")
    @classmethod
    def coverage_must_be_multiple_of_10000(cls, v: int) -> int:
        if v % 10000 != 0:
            raise ValueError("coverage_amount must be a multiple of 10000")
        return v

    @model_validator(mode='after')
    def validate_medical_details(self):
        if self.pre_existing_conditions and not self.medical_details:
            raise ValueError("medical_details is required when pre_existing_conditions is true")
        return self


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


@app.get("/applications/{application_id}")
def get_application(
    application_id: uuid.UUID,
    db_engine = Depends(get_db_engine)
) -> ApplicationResponse:
    """Retrieve an application by ID."""
    session = get_session(db_engine)
    try:
        application = get_application_by_id(session, str(application_id))
        if application is None:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Deserialize breakdown from JSON string
        breakdown = json.loads(application.breakdown)
        
        # SQLite stores datetimes without timezone, so add UTC timezone if missing
        created_at = application.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        
        return ApplicationResponse(
            application_id=application.id,
            status=application.status,
            quote=application.quote,
            breakdown=breakdown,
            reason=application.reason,
            submitted_at=created_at.isoformat()
        )
    finally:
        session.close()


@app.post("/applications", status_code=201)
def create_application(
    request: ApplicationRequest,
    db_engine = Depends(get_db_engine)
) -> ApplicationResponse:
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
    submitted_at = datetime.now(timezone.utc)
    
    # Save to database
    session = get_session(db_engine)
    try:
        application_data = {
            "id": application_id,
            "name": request.name,
            "age": request.age,
            "smoker": request.smoker,
            "coverage_amount": request.coverage_amount,
            "occupation": request.occupation,
            "pre_existing_conditions": request.pre_existing_conditions,
            "medical_details": request.medical_details,
            "status": pricing_result["status"],
            "quote": pricing_result["quote"],
            "breakdown": pricing_result["breakdown"],
            "reason": pricing_result["reason"],
            "created_at": submitted_at,
        }
        save_application(session, application_data)
    finally:
        session.close()
    
    # Combine pricing result with metadata
    return ApplicationResponse(
        application_id=application_id,
        status=pricing_result["status"],
        quote=pricing_result["quote"],
        breakdown=pricing_result["breakdown"],
        reason=pricing_result["reason"],
        submitted_at=submitted_at.isoformat()
    )
