from app.pricing import calculate_quote


def test_base_case():
    """25yo, non-smoker, low-risk, no conditions, £100k coverage"""
    result = calculate_quote(
        age=25,
        smoker=False,
        coverage_amount=100000,
        occupation="low_risk",
        pre_existing_conditions=False
    )
    assert result["status"] == "approved"
    assert result["quote"] == 500.00
    assert result["reason"] is None
    assert result["breakdown"]["base_premium"] == 500
    assert result["breakdown"]["coverage_multiplier"] == 1.0
    assert result["breakdown"]["age_multiplier"] == 1.0
    assert result["breakdown"]["smoker_multiplier"] == 1.0
    assert result["breakdown"]["occupation_multiplier"] == 1.0
    assert result["breakdown"]["pre_existing_conditions_multiplier"] == 1.0


def test_smoker():
    """25yo, smoker, low-risk, no conditions, £100k"""
    result = calculate_quote(
        age=25,
        smoker=True,
        coverage_amount=100000,
        occupation="low_risk",
        pre_existing_conditions=False
    )
    assert result["status"] == "approved"
    assert result["quote"] == 1000.00
    assert result["breakdown"]["smoker_multiplier"] == 2.0


def test_age_31():
    """31yo, non-smoker, low-risk, no conditions, £100k"""
    result = calculate_quote(
        age=31,
        smoker=False,
        coverage_amount=100000,
        occupation="low_risk",
        pre_existing_conditions=False
    )
    assert result["status"] == "approved"
    assert result["quote"] == 750.00
    assert result["breakdown"]["age_multiplier"] == 1.5


def test_age_51():
    """51yo, non-smoker, low-risk, no conditions, £100k"""
    result = calculate_quote(
        age=51,
        smoker=False,
        coverage_amount=100000,
        occupation="low_risk",
        pre_existing_conditions=False
    )
    assert result["status"] == "approved"
    assert result["quote"] == 1000.00
    assert result["breakdown"]["age_multiplier"] == 2.0


def test_age_66():
    """66yo, non-smoker, low-risk, no conditions, £100k"""
    result = calculate_quote(
        age=66,
        smoker=False,
        coverage_amount=100000,
        occupation="low_risk",
        pre_existing_conditions=False
    )
    assert result["status"] == "approved"
    assert result["quote"] == 1500.00
    assert result["breakdown"]["age_multiplier"] == 3.0


def test_medium_risk_occupation():
    """25yo, non-smoker, medium-risk, no conditions, £100k"""
    result = calculate_quote(
        age=25,
        smoker=False,
        coverage_amount=100000,
        occupation="medium_risk",
        pre_existing_conditions=False
    )
    assert result["status"] == "approved"
    assert result["quote"] == 650.00
    assert result["breakdown"]["occupation_multiplier"] == 1.3


def test_high_risk_occupation():
    """25yo, non-smoker, high-risk, no conditions, £100k"""
    result = calculate_quote(
        age=25,
        smoker=False,
        coverage_amount=100000,
        occupation="high_risk",
        pre_existing_conditions=False
    )
    assert result["status"] == "approved"
    assert result["quote"] == 900.00
    assert result["breakdown"]["occupation_multiplier"] == 1.8


def test_pre_existing_conditions():
    """25yo, non-smoker, low-risk, conditions, £100k - now referred"""
    result = calculate_quote(
        age=25,
        smoker=False,
        coverage_amount=100000,
        occupation="low_risk",
        pre_existing_conditions=True
    )
    assert result["status"] == "referred"
    assert result["quote"] is None
    assert result["reason"] is not None
    assert "breakdown" in result
    assert result["breakdown"]["pre_existing_conditions_multiplier"] == 1.5


def test_high_coverage():
    """25yo, non-smoker, low-risk, no conditions, £500k"""
    result = calculate_quote(
        age=25,
        smoker=False,
        coverage_amount=500000,
        occupation="low_risk",
        pre_existing_conditions=False
    )
    assert result["status"] == "approved"
    assert result["quote"] == 2500.00
    assert result["breakdown"]["coverage_multiplier"] == 5.0


def test_all_multipliers_combined():
    """66yo, smoker, medium-risk, no conditions, £500k"""
    result = calculate_quote(
        age=66,
        smoker=True,
        coverage_amount=500000,
        occupation="medium_risk",
        pre_existing_conditions=False
    )
    assert result["status"] == "approved"
    assert result["quote"] == 19500.00
    assert result["breakdown"]["coverage_multiplier"] == 5.0
    assert result["breakdown"]["age_multiplier"] == 3.0
    assert result["breakdown"]["smoker_multiplier"] == 2.0
    assert result["breakdown"]["occupation_multiplier"] == 1.3


def test_conditions_alone_referred():
    """Any application with conditions alone should be referred"""
    result = calculate_quote(
        age=30,
        smoker=False,
        coverage_amount=200000,
        occupation="medium_risk",
        pre_existing_conditions=True
    )
    assert result["status"] == "referred"
    assert result["quote"] is None
    assert result["reason"] is not None
    assert "breakdown" in result


def test_smoker_conditions_age_66_referred():
    """Smoker + conditions + age 66 returns referred with reason"""
    result = calculate_quote(
        age=66,
        smoker=True,
        coverage_amount=100000,
        occupation="low_risk",
        pre_existing_conditions=True
    )
    assert result["status"] == "referred"
    assert result["quote"] is None
    assert result["reason"] is not None
    assert "breakdown" in result
    assert result["breakdown"]["base_premium"] == 500


def test_high_risk_conditions_referred():
    """High-risk occupation + conditions returns referred (conditions rule applies)"""
    result = calculate_quote(
        age=25,
        smoker=False,
        coverage_amount=100000,
        occupation="high_risk",
        pre_existing_conditions=True
    )
    assert result["status"] == "referred"
    assert result["quote"] is None
    assert result["reason"] is not None
    assert "breakdown" in result


def test_smoker_high_risk_conditions_declined():
    """Smoker + high-risk occupation + conditions returns declined with reason"""
    result = calculate_quote(
        age=25,
        smoker=True,
        coverage_amount=100000,
        occupation="high_risk",
        pre_existing_conditions=True
    )
    assert result["status"] == "declined"
    assert result["quote"] is None
    assert result["reason"] is not None
    assert "breakdown" in result


def test_decline_takes_precedence_over_refer():
    """66yo, smoker, high-risk, conditions matches both decline and refer rules"""
    result = calculate_quote(
        age=66,
        smoker=True,
        coverage_amount=100000,
        occupation="high_risk",
        pre_existing_conditions=True
    )
    assert result["status"] == "declined"
    assert result["quote"] is None
    assert result["reason"] is not None
    assert "breakdown" in result
