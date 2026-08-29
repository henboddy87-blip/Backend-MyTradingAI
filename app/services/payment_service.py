import uuid
import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import Payment, Subscription, Plan, User
from app.core.logging import logger

class PaymentService:
    @classmethod
    def process_checkout(
        cls,
        db: Session,
        user: User,
        plan_id: int,
        provider: str = "mock",
        billing_period: str = "monthly"
    ) -> Dict[str, Any]:
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            raise ValueError("Plan not found")

        amount = plan.price_yearly if billing_period == "yearly" else plan.price_monthly
        tx_id = f"tx_{provider}_{uuid.uuid4().hex[:12]}"

        payment = Payment(
            user_id=user.id,
            plan_id=plan.id,
            amount=amount,
            currency="USD",
            provider=provider,
            status="COMPLETED", # In local mock mode, instantly completes
            transaction_id=tx_id,
            metadata_json={
                "billing_period": billing_period,
                "plan_code": plan.code,
                "plan_name": plan.name
            },
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.add(payment)

        # Update or create subscription
        now = datetime.datetime.now(datetime.timezone.utc)
        duration_days = 365 if billing_period == "yearly" else 30
        expires_at = now + datetime.timedelta(days=duration_days)

        subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
        if subscription:
            subscription.plan_id = plan.id  # type: ignore[assignment]
            subscription.status = "ACTIVE"  # type: ignore[assignment]
            subscription.started_at = now  # type: ignore[assignment]
            subscription.expires_at = expires_at  # type: ignore[assignment]
        else:
            subscription = Subscription(
                user_id=user.id,
                plan_id=plan.id,
                status="ACTIVE",
                started_at=now,
                expires_at=expires_at,
                auto_renew=True
            )
            db.add(subscription)

        db.commit()
        db.refresh(payment)
        logger.info(f"Processed {provider} payment of ${amount} for user {user.username} -> {plan.code}")

        return {
            "payment_id": payment.id,
            "transaction_id": tx_id,
            "status": "COMPLETED",
            "amount": amount,
            "plan_name": plan.name,
            "expires_at": expires_at.isoformat()
        }
