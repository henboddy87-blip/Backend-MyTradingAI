from app.services.risk_engine import RiskEngine

def test_valid_buy_risk_calculation():
    # Buy setup: Entry 2650, SL 2640, TP 2675 (R:R = 25 / 10 = 2.5)
    res = RiskEngine.calculate_position_risk(
        account_balance=10000.0,
        risk_percentage=1.0,
        entry=2650.0,
        stop_loss=2640.0,
        take_profit=2675.0,
        direction="BUY"
    )
    assert res.is_valid_risk is True
    assert res.risk_amount == 100.0
    assert res.reward_amount == 250.0
    assert res.risk_reward_ratio == 2.5
    assert len(res.warnings) == 0

def test_invalid_stop_loss():
    # Invalid: For a BUY, SL must be below entry
    res = RiskEngine.calculate_position_risk(
        account_balance=10000.0,
        risk_percentage=1.0,
        entry=2650.0,
        stop_loss=2660.0,
        take_profit=2680.0,
        direction="BUY"
    )
    assert res.is_valid_risk is False
    assert any("Stop Loss must be strictly below Entry" in w for w in res.warnings)

def test_suboptimal_risk_reward():
    # R:R = 5 / 10 = 0.5 (< 1.2 minimum)
    res = RiskEngine.calculate_position_risk(
        account_balance=10000.0,
        risk_percentage=1.0,
        entry=2650.0,
        stop_loss=2640.0,
        take_profit=2655.0,
        direction="BUY"
    )
    assert res.is_valid_risk is False
    assert any("Suboptimal Risk/Reward" in w for w in res.warnings)
