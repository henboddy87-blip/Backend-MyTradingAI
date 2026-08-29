from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.dependencies import get_current_active_user
from app.models.models import Mt5Account, Mt5Order, User
from app.schemas.schemas import Mt5AccountOut, Mt5OrderOut
from app.services.mt5_service import MT5Service
from app.market import get_market_data_provider

router = APIRouter(prefix="/mt5", tags=["MT5 Bridge"])

@router.get("/account", response_model=Mt5AccountOut)
def get_mt5_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return MT5Service.get_or_create_demo_account(db, current_user.id)

@router.get("/orders", response_model=List[Mt5OrderOut])
def get_mt5_orders(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    account = MT5Service.get_or_create_demo_account(db, current_user.id)
    return db.query(Mt5Order).filter(Mt5Order.account_id == account.id).order_by(Mt5Order.created_at.desc()).all()

@router.post("/order", response_model=Mt5OrderOut)
def execute_order(
    symbol: str = Body(..., embed=True),
    order_type: str = Body(..., embed=True), # BUY, SELL
    volume: float = Body(0.1, embed=True),
    sl: Optional[float] = Body(None, embed=True),
    tp: Optional[float] = Body(None, embed=True),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    account = MT5Service.get_or_create_demo_account(db, current_user.id)
    market_provider = get_market_data_provider()
    current_price = market_provider.get_latest_price(symbol.upper())

    order = MT5Service.simulate_order_execution(
        db=db,
        account=account,
        symbol=symbol,
        order_type=order_type,
        volume=volume,
        price=current_price,
        sl=sl,
        tp=tp
    )
    return order

@router.post("/order/{id}/close", response_model=Mt5OrderOut)
def close_mt5_order(
    id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    account = MT5Service.get_or_create_demo_account(db, current_user.id)
    order = db.query(Mt5Order).filter(
        Mt5Order.id == id,
        Mt5Order.account_id == account.id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    market_provider = get_market_data_provider()
    current_price = market_provider.get_latest_price(order.symbol)
    
    closed = MT5Service.close_order(db, order.id, current_price)
    return closed
