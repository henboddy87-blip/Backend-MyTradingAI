from app.services.signal_engine import SignalEngine
from app.models.models import Signal

def test_signal_generation_pipeline(db_session):
    sig = SignalEngine.generate_signal(db_session, "XAUUSD", "1h", "Medium")
    assert sig is not None
    assert sig.symbol == "XAUUSD"
    assert sig.direction in ["BUY", "SELL", "NO_TRADE"]
    if sig.direction != "NO_TRADE":
        assert sig.entry is not None
        assert sig.stop_loss is not None
        assert sig.take_profit_1 is not None
        assert sig.status == "ACTIVE"
    else:
        assert sig.status == "NO_TRADE"

def test_signal_lifecycle_evaluation(db_session):
    # Test evaluation of active signals
    updates = SignalEngine.evaluate_active_signals(db_session)
    assert isinstance(updates, list)
