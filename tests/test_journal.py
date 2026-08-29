from app.models.models import TradeJournal, User
from app.core.security import get_password_hash
from app.auth.jwt import create_access_token

def test_journal_crud_flow(client, db_session):
    # Create user
    user = User(
        full_name="Journal User",
        username="journaluser",
        email="journal@example.com",
        password_hash=get_password_hash("Pass123!"),
        role="USER",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": str(user.id), "username": user.username, "role": "USER"})
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create journal entry
    entry_payload = {
        "symbol": "XAUUSD",
        "direction": "BUY",
        "timeframe": "1h",
        "entry_price": 2650.0,
        "exit_price": 2675.0,
        "stop_loss": 2640.0,
        "take_profit": 2675.0,
        "position_size": 1.0,
        "profit_loss": 2500.0,
        "outcome": "WIN",
        "notes": "Followed AI council setup."
    }
    resp = client.post("/api/v1/journal/", json=entry_payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "XAUUSD"
    entry_id = data["id"]

    # 2. Get entries
    get_resp = client.get("/api/v1/journal/", headers=headers)
    assert get_resp.status_code == 200
    assert len(get_resp.json()) == 1

    # 3. Get stats
    stats_resp = client.get("/api/v1/journal/stats", headers=headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_trades"] == 1
    assert stats["wins"] == 1
    assert stats["win_rate"] == 100.0

    # 4. Delete entry
    del_resp = client.delete(f"/api/v1/journal/{entry_id}", headers=headers)
    assert del_resp.status_code == 200
