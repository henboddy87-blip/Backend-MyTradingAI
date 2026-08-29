from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.jwt import decode_token
from app.core.security import hash_api_key
from app.models.models import User, ApiKey, Subscription, Plan
from app.core.rate_limiter import rate_limiter

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    auth_token = token
    if not auth_token and authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split("Bearer ")[1].strip()

    if not auth_token:
        raise credentials_exception

    # 1. Check if token is an API key (starts with "mta_")
    if auth_token.startswith("mta_"):
        key_hash = hash_api_key(auth_token)
        api_key = db.query(ApiKey).filter(
            ApiKey.key_hash == key_hash,
            ApiKey.revoked_at.is_(None)
        ).first()

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked API Key"
            )

        # Enforce API Key rate limit
        rate_limiter.check_rate_limit(f"api_key_{api_key.id}", api_key.rate_limit_per_min)

        user = db.query(User).filter(User.id == api_key.user_id).first()
        if not user or not user.is_active:
            raise credentials_exception
        return user

    # 2. Check if token is JWT
    payload = decode_token(auth_token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise credentials_exception

    # Apply general rate limit based on role
    limit = 1000 if user.role == "ADMIN" else 120
    rate_limiter.check_rate_limit(f"user_{user.id}", limit)

    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")
    return current_user

def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required"
        )
    return current_user

def get_user_plan_code(user: User, db: Session) -> str:
    if user.role == "ADMIN":
        return "PREMIUM"
    sub = db.query(Subscription).join(Plan).filter(
        Subscription.user_id == user.id,
        Subscription.status == "ACTIVE"
    ).first()
    if sub and sub.plan:
        return sub.plan.code
    return "FREE"
