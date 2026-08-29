import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import Mt5Account, Mt5Order, Signal
from app.config import settings
from app.core.logging import logger

class MT5Service:
    @classmethod
    def get_or_create_demo_account(cls, db: Session, user_id: int) -> Mt5Account:
        account = db.query(Mt5Account).filter(Mt5Account.user_id == user_id).first()
        if not account:
            account = Mt5Account(
                user_id=user_id,
                account_number=f"DEMO-{user_id:04d}-MT5",
                broker="MetaQuotes-Demo",
                server="MyTradeAI-ExecutionBridge",
                is_connected=True,
                balance=10000.0,
                equity=10000.0,
                margin=0.0,
                free_margin=10000.0,
                live_trading_enabled=settings.MT5_LIVE_TRADING,
                last_heartbeat=datetime.datetime.now(datetime.timezone.utc)
            )
            db.add(account)
            db.commit()
            db.refresh(account)
        return account

    @classmethod
    def simulate_order_execution(
        cls,
        db: Session,
        account: Mt5Account,
        symbol: str,
        order_type: str,
        volume: float,
        price: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        signal_id: Optional[int] = None
    ) -> Mt5Order:
        order = Mt5Order(
            account_id=account.id,
            signal_id=signal_id,
            symbol=symbol.upper(),
            order_type=order_type.upper(),
            volume=volume,
            open_price=price,
            sl=sl,
            tp=tp,
            status="OPEN",
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.add(order)
        account.last_heartbeat = datetime.datetime.now(datetime.timezone.utc)  # type: ignore[assignment]
        db.commit()
        db.refresh(order)
        logger.info(f"[MT5 BRIDGE] Simulated execution of {order_type} {volume} lots {symbol} @ {price}")
        return order

    @classmethod
    def close_order(cls, db: Session, order_id: int, close_price: float) -> Optional[Mt5Order]:
        order = db.query(Mt5Order).filter(Mt5Order.id == order_id).first()
        if not order or order.status != "OPEN":
            return None

        profit = 0.0
        if order.order_type == "BUY":
            profit = (close_price - float(order.open_price)) * float(order.volume) * 100.0
        else:
            profit = (float(order.open_price) - close_price) * float(order.volume) * 100.0

        order.close_price = close_price  # type: ignore[assignment]
        order.profit = round(profit, 2)  # type: ignore[assignment]
        order.status = "CLOSED"  # type: ignore[assignment]
        order.closed_at = datetime.datetime.now(datetime.timezone.utc)  # type: ignore[assignment]

        account = db.query(Mt5Account).filter(Mt5Account.id == order.account_id).first()
        if account:
            account.balance += profit  # type: ignore[operator]
            account.equity = account.balance  # type: ignore[assignment]
            account.free_margin = account.balance  # type: ignore[assignment]

        db.commit()
        db.refresh(order)
        return order
