import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.dependencies import get_current_user, get_optional_user, get_current_admin_user, get_user_plan_code
from app.models.models import Signal, User
from app.schemas.schemas import SignalOut, SignalCreate, SignalUpdate, AIAnalyzeResponse
from app.services.signal_engine import SignalEngine
from app.services.telegram_service import TelegramService

router = APIRouter(prefix="/signals", tags=["Trading Signals"])

@router.get("/", response_model=List[SignalOut])
def get_signals(
    symbol: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    timeframe: Optional[str] = None,
    direction: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    query = db.query(Signal)
    
    if symbol and symbol.upper() != "ALL":
        query = query.filter(Signal.symbol == symbol.upper())
    if status_filter and status_filter.upper() != "ALL":
        query = query.filter(Signal.status == status_filter.upper())
    if timeframe and timeframe.lower() != "all":
        query = query.filter(Signal.timeframe == timeframe)
    if direction and direction.upper() != "ALL":
        query = query.filter(Signal.direction == direction.upper())

    signals = query.order_by(Signal.created_at.desc()).offset(offset).limit(limit).all()
    return [SignalOut.model_validate(s) for s in signals]

@router.get("/{id}", response_model=SignalOut)
def get_signal(
    id: int,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    s = db.query(Signal).filter(Signal.id == id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Signal not found")

    return SignalOut.model_validate(s)

@router.post("/generate-live", response_model=SignalOut)
async def generate_live_signal(
    symbol: str = Query(..., description="Asset symbol"),
    timeframe: str = Query("1h"),
    risk_level: str = Query("Medium"),
    is_pro_only: bool = Query(False),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Generates an institutional AI signal on demand from live exchange market data."""
    sig = SignalEngine.generate_signal(
        db, symbol=symbol.upper(), timeframe=timeframe, risk_level=risk_level, is_pro_only=is_pro_only
    )
    
    # Broadcast to Telegram if active and configured
    if sig.direction != "NO_TRADE":
        try:
            await TelegramService.send_signal_alert({
                "symbol": sig.symbol,
                "direction": sig.direction,
                "entry": sig.entry,
                "stop_loss": sig.stop_loss,
                "take_profit_1": sig.take_profit_1,
                "take_profit_2": sig.take_profit_2,
                "take_profit_3": sig.take_profit_3,
                "confidence": sig.confidence
            })
        except Exception:
            pass

    return SignalOut.model_validate(sig)

@router.post("/analyze-and-publish", response_model=SignalOut)
async def analyze_and_publish(
    symbol: str = Query(..., description="Asset symbol"),
    timeframe: str = Query("1h"),
    risk_level: str = Query("Medium"),
    is_pro_only: bool = Query(False),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    sig = SignalEngine.generate_signal(
        db, symbol=symbol.upper(), timeframe=timeframe, risk_level=risk_level, is_pro_only=is_pro_only
    )
    
    # Broadcast to Telegram if active
    if sig.direction != "NO_TRADE":
        await TelegramService.send_signal_alert({
            "symbol": sig.symbol,
            "direction": sig.direction,
            "entry": sig.entry,
            "stop_loss": sig.stop_loss,
            "take_profit_1": sig.take_profit_1,
            "take_profit_2": sig.take_profit_2,
            "take_profit_3": sig.take_profit_3,
            "confidence": sig.confidence
        })

    return SignalOut.model_validate(sig)

@router.post("/publish-from-analysis", response_model=SignalOut)
async def publish_from_analysis(
    req: AIAnalyzeResponse,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    if req.direction == "NO_TRADE" or not req.entry:
        raise HTTPException(status_code=400, detail="Cannot generate an active signal for a NO_TRADE setup.")
    
    from app.models.models import Asset
    asset = db.query(Asset).filter(Asset.symbol == req.symbol.upper()).first()
    market_type = str(asset.market_type) if asset and asset.market_type else "crypto"
    
    now = datetime.datetime.now(datetime.timezone.utc)
    sig = Signal(
        symbol=req.symbol.upper(),
        market_type=market_type,
        timeframe=req.timeframe,
        direction=req.direction,
        entry=req.entry,
        stop_loss=req.stop_loss,
        take_profit_1=req.take_profit_1,
        take_profit_2=req.take_profit_2,
        take_profit_3=req.take_profit_3,
        confidence=req.confidence,
        risk_reward=req.risk_reward,
        bias=req.market_bias,
        technical_summary=str(req.technical_analysis),
        sentiment_summary=str(req.news_sentiment),
        risk_assessment=req.risk_assessment,
        reasoning=req.reasoning,
        analyst_votes_json={k: (v.model_dump() if hasattr(v, 'model_dump') else (v.dict() if hasattr(v, 'dict') else v)) for k, v in req.analyst_votes.items()},
        status="ACTIVE",
        is_pro_only=False,
        created_at=now,
        published_at=now
    )
    db.add(sig)
    db.commit()
    db.refresh(sig)
    return SignalOut.model_validate(sig)

@router.post("/", response_model=SignalOut, status_code=status.HTTP_201_CREATED)
def create_custom_signal(
    req: SignalCreate,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    from app.models.models import Asset
    asset = db.query(Asset).filter(Asset.symbol == req.symbol.upper()).first()
    market_type = str(asset.market_type) if asset and asset.market_type else req.market_type
    
    now = datetime.datetime.now(datetime.timezone.utc)
    sig = Signal(
        symbol=req.symbol.upper(),
        market_type=market_type,
        timeframe=req.timeframe,
        direction=req.direction,
        entry=req.entry,
        stop_loss=req.stop_loss,
        take_profit_1=req.take_profit_1,
        take_profit_2=req.take_profit_2,
        take_profit_3=req.take_profit_3,
        confidence=req.confidence,
        risk_reward=req.risk_reward,
        bias=req.bias,
        technical_summary=req.technical_summary or f"Manual user strategy execution on {req.symbol}",
        sentiment_summary=req.sentiment_summary,
        risk_assessment=req.risk_assessment,
        reasoning=req.reasoning or f"Custom trader setup for {req.symbol} ({req.timeframe})",
        analyst_votes_json=req.analyst_votes or {},
        status="ACTIVE" if req.direction != "NO_TRADE" else "NO_TRADE",
        is_pro_only=req.is_pro_only,
        created_at=now,
        published_at=now
    )
    db.add(sig)
    db.commit()
    db.refresh(sig)
    return SignalOut.model_validate(sig)

@router.put("/{id}", response_model=SignalOut)
def update_signal(
    id: int,
    req: SignalUpdate,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    sig = db.query(Signal).filter(Signal.id == id).first()
    if not sig:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    if req.entry is not None:
        setattr(sig, "entry", req.entry)
    if req.stop_loss is not None:
        setattr(sig, "stop_loss", req.stop_loss)
    if req.take_profit_1 is not None:
        setattr(sig, "take_profit_1", req.take_profit_1)
    if req.take_profit_2 is not None:
        setattr(sig, "take_profit_2", req.take_profit_2)
    if req.take_profit_3 is not None:
        setattr(sig, "take_profit_3", req.take_profit_3)
    if req.status is not None:
        setattr(sig, "status", req.status)
        if req.status in ["CLOSED", "CANCELLED", "TP1_HIT", "TP2_HIT", "TP3_HIT", "SL_HIT"]:
            setattr(sig, "closed_at", datetime.datetime.now(datetime.timezone.utc))
    if req.reasoning is not None:
        setattr(sig, "reasoning", req.reasoning)

    db.commit()
    db.refresh(sig)
    return SignalOut.model_validate(sig)

@router.delete("/{id}")
def delete_signal(
    id: int,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    sig = db.query(Signal).filter(Signal.id == id).first()
    if not sig:
        raise HTTPException(status_code=404, detail="Signal not found")
    db.delete(sig)
    db.commit()
    return {"message": f"Signal #{id} deleted successfully"}

@router.post("/clear-all")
def clear_all_signals(
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Clears all existing default / seed signals so user starts with 100% clean workspace.
    """
    deleted_count = db.query(Signal).delete()
    db.commit()
    return {"message": f"Successfully cleared {deleted_count} signals. Workspace is 100% clean."}

@router.post("/auto-generate", response_model=List[SignalOut])
def auto_generate_market_signals(
    count: int = Query(5, ge=1, le=30, description="Number of signals to generate (5, 20, or 30)"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    signals = SignalEngine.auto_scan_and_generate_signals(db, target_count=count)
    return [SignalOut.model_validate(s) for s in signals]

@router.post("/{id}/void")
def void_signal(id: int, current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    sig = db.query(Signal).filter(Signal.id == id).first()
    if not sig:
        raise HTTPException(status_code=404, detail="Signal not found")
    setattr(sig, "status", "CANCELLED")
    setattr(sig, "closed_at", datetime.datetime.now(datetime.timezone.utc))
    db.commit()
    return {"message": f"Signal #{id} has been cancelled/voided"}
