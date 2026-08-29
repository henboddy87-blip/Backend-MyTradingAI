from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.dependencies import get_current_active_user
from app.models.models import Watchlist, Asset, Signal, User
from app.schemas.schemas import WatchlistCreate, WatchlistOut
from app.market import get_market_data_provider

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])

@router.get("/", response_model=List[WatchlistOut])
def get_watchlist(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    items = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).all()
    market_provider = get_market_data_provider()
    
    result = []
    for item in items:
        sym = item.symbol.upper()
        ticker = market_provider.get_ticker(sym)
        asset = db.query(Asset).filter(Asset.symbol == sym).first()
        latest_sig = db.query(Signal).filter(Signal.symbol == sym).order_by(Signal.created_at.desc()).first()

        result.append(WatchlistOut(
            id=item.id,
            symbol=sym,
            asset_name=asset.name if asset else ticker.get("name", sym),
            market_type=asset.market_type if asset else ticker.get("market_type", "crypto"),
            current_price=ticker.get("price", 0.0),
            change_24h=ticker.get("change_24h", 0.0),
            ai_bias=latest_sig.bias if latest_sig else "neutral",
            latest_signal=latest_sig.direction if latest_sig else None,
            created_at=item.created_at
        ))

    return result

@router.post("/", response_model=WatchlistOut)
def add_to_watchlist(
    req: WatchlistCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    sym = req.symbol.upper()
    existing = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.symbol == sym
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Symbol already in watchlist")

    item = Watchlist(user_id=current_user.id, symbol=sym)
    db.add(item)
    db.commit()
    db.refresh(item)

    market_provider = get_market_data_provider()
    ticker = market_provider.get_ticker(sym)
    asset = db.query(Asset).filter(Asset.symbol == sym).first()

    return WatchlistOut(
        id=item.id,
        symbol=sym,
        asset_name=asset.name if asset else sym,
        market_type=asset.market_type if asset else "crypto",
        current_price=ticker.get("price", 0.0),
        change_24h=ticker.get("change_24h", 0.0),
        ai_bias="neutral",
        latest_signal=None,
        created_at=item.created_at
    )

@router.delete("/{symbol}")
def remove_from_watchlist(
    symbol: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    item = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.symbol == symbol.upper()
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Symbol not found in watchlist")

    db.delete(item)
    db.commit()
    return {"message": f"{symbol.upper()} removed from watchlist"}
