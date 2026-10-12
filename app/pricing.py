# Pricing constants
BASE_PREMIUM = 500

# Age multipliers by age range
AGE_MULTIPLIERS = {
    (18, 30): 1.0,
    (31, 50): 1.5,
    (51, 65): 2.0,
    (66, 80): 3.0,
}

# Occupation multipliers
OCCUPATION_MULTIPLIERS = {
    "low_risk": 1.0,
    "medium_risk": 1.3,
    "high_risk": 1.8,
}

# Other multipliers
SMOKER_MULTIPLIER = 2.0
PRE_EXISTING_CONDITIONS_MULTIPLIER = 1.5


def get_age_multiplier(age: int) -> float:
    """Get the age multiplier based on age bracket."""
    for (min_age, max_age), multiplier in AGE_MULTIPLIERS.items():
        if min_age <= age <= max_age:
            return multiplier
    return 1.0


def check_decline_rules(
    age: int,
    smoker: bool,
    occupation: str,
    pre_existing_conditions: bool
) -> tuple[bool, str | None]:
    """Check if application should be declined. Returns (is_declined, reason)."""
    if smoker and occupation == "high_risk" and pre_existing_conditions:
        return True, "Application declined: combination of smoker, high-risk occupation, and pre-existing conditions"
    return False, None


def check_refer_rules(
    age: int,
    smoker: bool,
    occupation: str,
    pre_existing_conditions: bool
) -> tuple[bool, str | None]:
    """Check if application should be referred. Returns (is_referred, reason)."""
    if smoker and pre_existing_conditions and age > 65:
        return True, "Application referred: smoker with pre-existing conditions over age 65"
    if occupation == "high_risk" and pre_existing_conditions:
        return True, "Application referred: high-risk occupation with pre-existing conditions"
    return False, None


def calculate_premium(
    age: int,
    smoker: bool,
    coverage_amount: int,
    occupation: str,
    pre_existing_conditions: bool
) -> tuple[float, dict]:
    """Calculate premium and return (quote_amount, breakdown_dict)."""
    coverage_multiplier = coverage_amount / 100000
    age_multiplier = get_age_multiplier(age)
    smoker_multiplier = SMOKER_MULTIPLIER if smoker else 1.0
    occupation_multiplier = OCCUPATION_MULTIPLIERS[occupation]
    conditions_multiplier = PRE_EXISTING_CONDITIONS_MULTIPLIER if pre_existing_conditions else 1.0
    
    quote = BASE_PREMIUM * coverage_multiplier * age_multiplier * smoker_multiplier * occupation_multiplier * conditions_multiplier
    
    breakdown = {
        "base_premium": BASE_PREMIUM,
        "coverage_multiplier": coverage_multiplier,
        "age_multiplier": age_multiplier,
        "smoker_multiplier": smoker_multiplier,
        "occupation_multiplier": occupation_multiplier,
        "pre_existing_conditions_multiplier": conditions_multiplier,
    }
    
    return round(quote, 2), breakdown


def calculate_quote(
    age: int,
    smoker: bool,
    coverage_amount: int,
    occupation: str,
    pre_existing_conditions: bool
) -> dict:
    """
    Calculate insurance quote and determine approval status.
    
    Returns dict with status, quote, breakdown, and reason.
    Precedence: declined first, then referred, then approved.
    """
    # Always calculate premium and breakdown for transparency
    quote_amount, breakdown = calculate_premium(
        age, smoker, coverage_amount, occupation, pre_existing_conditions
    )
    
    # Check decline rules first (highest precedence)
    is_declined, decline_reason = check_decline_rules(
        age, smoker, occupation, pre_existing_conditions
    )
    if is_declined:
        return {
            "status": "declined",
            "quote": None,
            "breakdown": breakdown,
            "reason": decline_reason,
        }
    
    # Check refer rules second
    is_referred, refer_reason = check_refer_rules(
        age, smoker, occupation, pre_existing_conditions
    )
    if is_referred:
        return {
            "status": "referred",
            "quote": None,
            "breakdown": breakdown,
            "reason": refer_reason,
        }
    
    # Approved (default case)
    return {
        "status": "approved",
        "quote": quote_amount,
        "breakdown": breakdown,
        "reason": None,
    }
