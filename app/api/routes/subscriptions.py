from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.dependencies import get_current_active_user
from app.models.models import Plan, Subscription, User
from app.schemas.schemas import PlanOut, SubscriptionOut, PaymentCreate, PaymentOut
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/subscription", tags=["Subscriptions & Billing"])

@router.get("/plans", response_model=List[PlanOut])
def get_plans(db: Session = Depends(get_db)):
    return db.query(Plan).filter(Plan.is_active == True).all()

@router.get("/current", response_model=Optional[SubscriptionOut])
def get_current_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    sub = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "ACTIVE"
    ).first()
    
    if not sub:
        # Return default FREE subscription structure
        free_plan = db.query(Plan).filter(Plan.code == "FREE").first()
        if not free_plan:
            return None
        return SubscriptionOut(
            id=0,
            user_id=current_user.id,
            plan=PlanOut.from_orm(free_plan),
            status="ACTIVE",
            started_at=current_user.created_at,
            expires_at=None,
            auto_renew=True
        )

    return SubscriptionOut(
        id=sub.id,
        user_id=sub.user_id,
        plan=PlanOut.from_orm(sub.plan),
        status=sub.status,
        started_at=sub.started_at,
        expires_at=sub.expires_at,
        auto_renew=sub.auto_renew
    )

@router.post("/checkout")
def create_checkout(
    req: PaymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    result = PaymentService.process_checkout(
        db,
        user=current_user,
        plan_id=req.plan_id,
        provider=req.provider,
        billing_period=req.billing_period
    )
    return result
