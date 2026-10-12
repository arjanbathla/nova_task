# Insurance Application System

A REST API that validates insurance applications, calculates risk-based premiums, and stores applications with quotes in a database.

## Input Fields

- **name**: string, 1-100 chars (required for identification)
- **age**: integer, 18-80 (legal age limits - validation error if outside)
- **smoker**: boolean (major risk factor)
- **coverage_amount**: integer, 50000-1000000, multiples of 10000 (product limits)
- **occupation**: enum ["low_risk", "medium_risk", "high_risk"] (actuarial categories)
- **pre_existing_conditions**: boolean (underwriting requirement)

## Pricing

- **Base premium**: £500/year (UK market baseline)
- **Coverage multiplier**: coverage_amount / 100000 (scales linearly with coverage)
- **Age multiplier**: 
  - 18-30: 1.0 (lowest risk group)
  - 31-50: 1.5 (moderate risk increase)
  - 51-65: 2.0 (higher risk)
  - 66-80: 3.0 (highest risk group)
- **Smoker multiplier**: 2.0 (doubles premium due to health risks)
- **Occupation multiplier**:
  - low_risk: 1.0 (office workers)
  - medium_risk: 1.3 (moderate physical labor)
  - high_risk: 1.8 (dangerous professions)
- **Pre-existing conditions multiplier**: 1.5 (increased medical risk)
- **Formula**: base × coverage_multiplier × age_multiplier × smoker_multiplier × occupation_multiplier × pre_existing_conditions_multiplier

## Decline/Refer Cases

- **Smoker + pre_existing_conditions + age > 65**: REFERRED (too high risk for auto-approval)
- **High_risk occupation + pre_existing_conditions**: REFERRED (needs manual underwriting review)
- **Smoker + high_risk occupation + pre_existing_conditions**: DECLINED (unacceptable risk combination)

## Response Format

- **application_id**: UUID (unique identifier for tracking)
- **status**: "approved", "declined", "referred" (application outcome)
- **quote**: float or null (annual premium in GBP if approved, null otherwise)
- **breakdown**: object with base_premium and each multiplier applied (transparency for customer)
- **reason**: string or null (explanation for declined/referred)
- **submitted_at**: ISO timestamp (audit trail)

## Storage

- **SQLite**: Simple, file-based database
- **Table**: applications (id, name, age, smoker, coverage_amount, occupation, pre_existing_conditions, status, quote, reason, created_at)

## Code Structure

```
app/
  main.py           # FastAPI app, routes, Pydantic models
  pricing.py        # Pure functions for pricing logic and decline/refer rules
  models.py         # SQLAlchemy models
  db.py             # Database connection and session management
tests/
  test_pricing.py   # Unit tests for pricing logic
  test_api.py       # Integration tests for API endpoints
requirements.txt    # Dependencies list
```

## API Endpoints

### POST /applications
Submit an insurance application.

- **201**: Created (approved/declined/referred - all valid outcomes)
- **422**: Validation error (invalid input - age out of range, invalid coverage, etc.)

### GET /applications/{id}
Retrieve an application by ID.

- **200**: Found
- **404**: Not found
