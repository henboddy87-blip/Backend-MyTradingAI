from app.core.security import get_password_hash, verify_password
from app.auth.jwt import create_access_token, decode_token

def test_password_hashing():
    pwd = "SecretTradingPassword123!"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_flow():
    payload = {"sub": "42", "username": "trader_quant", "role": "USER"}
    token = create_access_token(payload)
    assert isinstance(token, str)
    decoded = decode_token(token)
    assert decoded is not None
    assert decoded["sub"] == "42"
    assert decoded["username"] == "trader_quant"

def test_user_registration_and_login(client):
    # 1. Register new user
    reg_data = {
        "full_name": "Test Trader",
        "username": "testtrader",
        "email": "testtrader@example.com",
        "password": "SecurePassword123!",
        "country": "Germany"
    }
    response = client.post("/api/v1/auth/register", json=reg_data)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "testtrader"
    assert data["user"]["email"] == "testtrader@example.com"

    # 2. Login with registered credentials
    login_data = {
        "username_or_email": "testtrader",
        "password": "SecurePassword123!"
    }
    login_resp = client.post("/api/v1/auth/login", json=login_data)
    assert login_resp.status_code == 200
    login_json = login_resp.json()
    assert "access_token" in login_json
    token = login_json["access_token"]

    # 3. Access protected /me endpoint
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "testtrader"
