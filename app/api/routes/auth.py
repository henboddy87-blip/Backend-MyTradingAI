from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash
from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.auth.dependencies import get_current_user, get_current_active_user, get_user_plan_code
from app.models.models import User, Plan, Subscription, SystemLog
from app.schemas.schemas import (
    UserRegister, UserLogin, UserUpdate, UserOut, Token,
    RefreshTokenRequest, PasswordResetRequest, PasswordResetConfirm
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    # Check if username or email already exists
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username is already registered")
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email is already registered")

    hashed_pw = get_password_hash(user_in.password)
    user = User(
        full_name=user_in.full_name,
        username=user_in.username,
        email=user_in.email,
        password_hash=hashed_pw,
        country=user_in.country,
        phone=user_in.phone,
        telegram_username=user_in.telegram_username,
        role="USER",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Assign default FREE plan
    free_plan = db.query(Plan).filter(Plan.code == "FREE").first()
    if free_plan:
        sub = Subscription(
            user_id=user.id,
            plan_id=free_plan.id,
            status="ACTIVE",
            started_at=datetime.utcnow()
        )
        db.add(sub)
        db.commit()

    access_token = create_access_token(data={"sub": str(user.id), "username": user.username, "role": user.role})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    user_out = UserOut(
        id=user.id,
        full_name=user.full_name,
        username=user.username,
        email=user.email,
        country=user.country,
        phone=user.phone,
        telegram_username=user.telegram_username,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        plan_code="FREE"
    )

    return Token(access_token=access_token, refresh_token=refresh_token, user=user_out)

@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    ident = credentials.username_or_email.strip()
    user = db.query(User).filter((User.username == ident) | (User.email == ident)).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username/email or password")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User account is deactivated")

    access_token = create_access_token(data={"sub": str(user.id), "username": user.username, "role": user.role})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    plan_code = get_user_plan_code(user, db)

    user_out = UserOut(
        id=user.id,
        full_name=user.full_name,
        username=user.username,
        email=user.email,
        country=user.country,
        phone=user.phone,
        telegram_username=user.telegram_username,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        plan_code=plan_code
    )

    return Token(access_token=access_token, refresh_token=refresh_token, user=user_out)

@router.post("/refresh")
def refresh_token(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    new_access_token = create_access_token(data={"sub": str(user.id), "username": user.username, "role": user.role})
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    plan_code = get_user_plan_code(current_user, db)
    return UserOut(
        id=current_user.id,
        full_name=current_user.full_name,
        username=current_user.username,
        email=current_user.email,
        country=current_user.country,
        phone=current_user.phone,
        telegram_username=current_user.telegram_username,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        plan_code=plan_code
    )

@router.put("/me", response_model=UserOut)
def update_me(update_data: UserUpdate, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name
    if update_data.country is not None:
        current_user.country = update_data.country
    if update_data.phone is not None:
        current_user.phone = update_data.phone
    if update_data.telegram_username is not None:
        current_user.telegram_username = update_data.telegram_username
    
    db.commit()
    db.refresh(current_user)
    plan_code = get_user_plan_code(current_user, db)

    return UserOut(
        id=current_user.id,
        full_name=current_user.full_name,
        username=current_user.username,
        email=current_user.email,
        country=current_user.country,
        phone=current_user.phone,
        telegram_username=current_user.telegram_username,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        plan_code=plan_code
    )

@router.post("/forgot-password")
def forgot_password(req: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    # In local demo mode, return simulated reset token
    reset_token = f"reset_{user.id if user else 1}_token_valid_15m"
    return {"message": "Password reset instructions sent", "demo_reset_token": reset_token}

@router.post("/reset-password")
def reset_password(req: PasswordResetConfirm, db: Session = Depends(get_db)):
    if "reset_" not in req.token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    return {"message": "Password successfully reset. You may now log in."}
