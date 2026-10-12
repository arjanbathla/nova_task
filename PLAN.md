# Build Plan

## Ticket 1: Project skeleton with passing test
- [ ] **Goal**: Set up FastAPI app with health check endpoint
- [ ] **Files**: app/main.py, requirements.txt, tests/test_api.py
- [ ] **Tests**: 
  - GET /health returns 200 with {"status": "ok"}
- [ ] **Why first**: Validates environment setup, FastAPI works, test framework configured

## Ticket 2: Pricing engine as pure functions
- [ ] **Goal**: Calculate quotes and determine approve/decline/refer status
- [ ] **Files**: app/pricing.py, tests/test_pricing.py
- [ ] **Tests**: 
  - Base case (25yo, non-smoker, low-risk, no conditions, £100k coverage) returns approved with quote of £500.00
  - Smoker (25yo, smoker, low-risk, no conditions, £100k) returns approved with quote of £1000.00
  - Age 31 (31yo, non-smoker, low-risk, no conditions, £100k) returns approved with quote of £750.00
  - Age 51 (51yo, non-smoker, low-risk, no conditions, £100k) returns approved with quote of £1000.00
  - Age 66 (66yo, non-smoker, low-risk, no conditions, £100k) returns approved with quote of £1500.00
  - Medium risk occupation (25yo, non-smoker, medium-risk, no conditions, £100k) returns approved with quote of £650.00
  - High risk occupation (25yo, non-smoker, high-risk, no conditions, £100k) returns approved with quote of £900.00
  - Pre-existing conditions (25yo, non-smoker, low-risk, conditions, £100k) returns approved with quote of £750.00
  - High coverage (25yo, non-smoker, low-risk, no conditions, £500k) returns approved with quote of £2500.00
  - All multipliers combined (66yo, smoker, high-risk, conditions, £500k) returns approved with quote of £40500.00
  - Smoker + conditions + age 66 returns referred with reason
  - High-risk occupation + conditions returns referred with reason
  - Smoker + high-risk occupation + conditions returns declined with reason
  - Breakdown includes base_premium and all applied multipliers with their values
- [ ] **Why second**: Core business logic isolated, testable without database or HTTP

## Ticket 3: POST /applications endpoint
- [ ] **Goal**: Wire pricing logic into API with Pydantic validation
- [ ] **Files**: app/main.py (add Pydantic models and endpoint), tests/test_api.py
- [ ] **Tests**: 
  - Valid application returns 201 with quote and breakdown
  - Age 17 returns 422 validation error
  - Age 81 returns 422 validation error
  - Coverage £40000 returns 422 validation error
  - Coverage £1100000 returns 422 validation error
  - Coverage not multiple of £10000 returns 422 validation error
  - Missing required field (name) returns 422
  - Invalid occupation value returns 422
  - Referred case returns 201 with status="referred" and reason
  - Declined case returns 201 with status="declined" and reason
- [ ] **Why third**: Pydantic handles validation, integrates pricing logic into HTTP layer

## Ticket 4: SQLite storage layer
- [ ] **Goal**: Persist applications to database
- [ ] **Files**: app/models.py, app/db.py, update app/main.py to save to DB
- [ ] **Tests**: 
  - POST creates record in temporary test database
  - Saved application has all fields persisted correctly (name, age, smoker, coverage_amount, occupation, pre_existing_conditions, status, quote, reason)
  - Application ID is UUID and returned in response
  - Timestamp is set automatically
- [ ] **Why fourth**: Storage is independent concern, can be added after core logic works

## Ticket 5: GET /applications/{id} endpoint
- [ ] **Goal**: Retrieve stored applications by ID
- [ ] **Files**: app/main.py (add GET endpoint), tests/test_api.py
- [ ] **Tests**: 
  - Existing application returns 200 with all fields matching what was saved
  - Non-existent UUID returns 404
  - Invalid UUID format returns 422
  - Uses temporary test database
- [ ] **Why fifth**: Read-only feature, depends on storage layer, less critical than write path

## Ticket 6: Simple UI
- [ ] **Goal**: Add a web form to submit applications and display results
- [ ] **Files**: static/index.html, app/main.py (mount static files and add GET / endpoint), tests/test_api.py
- [ ] **Tests**: 
  - GET / returns 200 and contains form with all input fields (name, age, smoker, coverage_amount, occupation, pre_existing_conditions)
- [ ] **Why last**: UI depends on the API being complete, and all business rules stay in the backend
