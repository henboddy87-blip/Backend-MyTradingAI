from app.models.models import User
from app.core.security import get_password_hash
from app.auth.jwt import create_access_token

def test_mcp_json_rpc_tools(client, db_session):
    user = User(
        full_name="MCP User",
        username="mcpuser",
        email="mcp@example.com",
        password_hash=get_password_hash("Pass123!"),
        role="ADMIN",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": str(user.id), "username": user.username, "role": "ADMIN"})
    headers = {"Authorization": f"Bearer {token}"}

    # 1. List tools
    rpc_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    resp = client.post("/api/mcp/", json=rpc_req, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "result" in data
    assert "tools" in data["result"]
    tool_names = [t["name"] for t in data["result"]["tools"]]
    assert "latest_signals" in tool_names
    assert "track_record" in tool_names
    assert "desk_read" in tool_names

    # 2. Call desk_read
    desk_req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "desk_read",
        "params": {}
    }
    desk_resp = client.post("/api/mcp/", json=desk_req, headers=headers)
    assert desk_resp.status_code == 200
    desk_json = desk_resp.json()
    assert "result" in desk_json
    assert "market_regime" in desk_json["result"]
