import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.dependencies import get_current_admin_user
from app.models.models import User, Signal, Subscription, Payment, Plan, SystemLog, Asset
from app.schemas.schemas import UserOut, SignalOut, SystemLogOut

router = APIRouter(prefix="/admin", tags=["Admin Controls"])

# Shared engine status state
ENGINE_STATE = {
    "is_ai_scanning_active": True,
    "is_auto_trading_active": True,
    "last_toggled_at": datetime.datetime.utcnow().isoformat()
}

@router.get("/stats")
def get_admin_stats(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    total_users = db.query(User).count()
    total_signals = db.query(Signal).count()
    active_signals = db.query(Signal).filter(Signal.status.in_(["ACTIVE", "TP1_HIT", "TP2_HIT"])).count()
    completed_payments = db.query(Payment).filter(Payment.status == "COMPLETED").all()
    total_revenue = sum(p.amount for p in completed_payments)
    active_subs = db.query(Subscription).filter(Subscription.status == "ACTIVE").count()

    return {
        "total_users": total_users,
        "total_signals": total_signals,
        "active_signals": active_signals,
        "total_revenue": round(total_revenue, 2),
        "active_subscriptions": active_subs,
        "ai_engine_active": ENGINE_STATE["is_ai_scanning_active"],
        "auto_trading_active": ENGINE_STATE["is_auto_trading_active"]
    }

@router.get("/users", response_model=List[UserOut])
def get_all_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    users = db.query(User).order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    result = []
    for u in users:
        sub = db.query(Subscription).filter(Subscription.user_id == u.id, Subscription.status == "ACTIVE").first()
        plan_code = sub.plan.code if sub and sub.plan else "FREE"
        result.append(UserOut(
            id=u.id,
            full_name=u.full_name,
            username=u.username,
            email=u.email,
            country=u.country,
            phone=u.phone,
            telegram_username=u.telegram_username,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at,
            plan_code=plan_code
        ))
    return result

@router.put("/users/{id}")
def update_user_status(
    id: int,
    is_active: Optional[bool] = Body(None, embed=True),
    role: Optional[str] = Body(None, embed=True),
    plan_code: Optional[str] = Body(None, embed=True),
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if is_active is not None:
        user.is_active = is_active
    if role is not None and role in ["USER", "ADMIN"]:
        user.role = role

    if plan_code:
        plan = db.query(Plan).filter(Plan.code == plan_code.upper()).first()
        if plan:
            sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
            if sub:
                sub.plan_id = plan.id
                sub.status = "ACTIVE"
            else:
                sub = Subscription(user_id=user.id, plan_id=plan.id, status="ACTIVE")
                db.add(sub)

    db.commit()
    return {"message": f"User {user.username} updated successfully"}

@router.post("/engine/toggle")
def toggle_engine(
    feature: str = Body(..., embed=True), # "ai_scanning" or "auto_trading"
    admin_user: User = Depends(get_current_admin_user)
):
    if feature == "ai_scanning":
        ENGINE_STATE["is_ai_scanning_active"] = not ENGINE_STATE["is_ai_scanning_active"]
    elif feature == "auto_trading":
        ENGINE_STATE["is_auto_trading_active"] = not ENGINE_STATE["is_auto_trading_active"]
    ENGINE_STATE["last_toggled_at"] = datetime.datetime.utcnow().isoformat()
    return ENGINE_STATE

@router.get("/logs", response_model=List[SystemLogOut])
def get_system_logs(
    limit: int = Query(50, ge=1, le=100),
    level: Optional[str] = None,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    query = db.query(SystemLog)
    if level and level.upper() != "ALL":
        query = query.filter(SystemLog.level == level.upper())
    return query.order_by(SystemLog.created_at.desc()).limit(limit).all()
