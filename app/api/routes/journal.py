import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.dependencies import get_current_active_user
from app.models.models import TradeJournal, User
from app.schemas.schemas import JournalCreate, JournalUpdate, JournalOut, JournalStatsOut

router = APIRouter(prefix="/journal", tags=["Trade Journal"])

@router.get("/", response_model=List[JournalOut])
def get_journal_entries(
    symbol: Optional[str] = None,
    outcome: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(TradeJournal).filter(TradeJournal.user_id == current_user.id)
    if symbol and symbol.upper() != "ALL":
        query = query.filter(TradeJournal.symbol == symbol.upper())
    if outcome and outcome.upper() != "ALL":
        query = query.filter(TradeJournal.outcome == outcome.upper())

    return query.order_by(TradeJournal.trade_date.desc()).all()

@router.post("/", response_model=JournalOut)
def create_journal_entry(
    entry_in: JournalCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Calculate initial pnl_r if SL and TP exist
    pnl_r = 0.0
    if entry_in.stop_loss and entry_in.exit_price:
        risk_dist = abs(entry_in.entry_price - entry_in.stop_loss)
        if risk_dist > 0:
            if entry_in.direction == "BUY":
                pnl_r = round((entry_in.exit_price - entry_in.entry_price) / risk_dist, 2)
            else:
                pnl_r = round((entry_in.entry_price - entry_in.exit_price) / risk_dist, 2)

    entry = TradeJournal(
        user_id=current_user.id,
        symbol=entry_in.symbol.upper(),
        direction=entry_in.direction.upper(),
        timeframe=entry_in.timeframe,
        entry_price=entry_in.entry_price,
        exit_price=entry_in.exit_price,
        stop_loss=entry_in.stop_loss,
        take_profit=entry_in.take_profit,
        position_size=entry_in.position_size,
        profit_loss=entry_in.profit_loss,
        pnl_r=pnl_r,
        outcome=entry_in.outcome.upper(),
        notes=entry_in.notes,
        screenshot_url=entry_in.screenshot_url,
        tags=entry_in.tags,
        trade_date=entry_in.trade_date or datetime.datetime.utcnow()
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

@router.put("/{id}", response_model=JournalOut)
def update_journal_entry(
    id: int,
    update_in: JournalUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    entry = db.query(TradeJournal).filter(
        TradeJournal.id == id,
        TradeJournal.user_id == current_user.id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    if update_in.exit_price is not None:
        entry.exit_price = update_in.exit_price
    if update_in.profit_loss is not None:
        entry.profit_loss = update_in.profit_loss
    if update_in.outcome is not None:
        entry.outcome = update_in.outcome.upper()
    if update_in.notes is not None:
        entry.notes = update_in.notes
    if update_in.screenshot_url is not None:
        entry.screenshot_url = update_in.screenshot_url
    if update_in.tags is not None:
        entry.tags = update_in.tags

    # Recalculate pnl_r
    if entry.stop_loss and entry.exit_price:
        risk_dist = abs(entry.entry_price - entry.stop_loss)
        if risk_dist > 0:
            if entry.direction == "BUY":
                entry.pnl_r = round((entry.exit_price - entry.entry_price) / risk_dist, 2)
            else:
                entry.pnl_r = round((entry.entry_price - entry.exit_price) / risk_dist, 2)

    db.commit()
    db.refresh(entry)
    return entry

@router.delete("/{id}")
def delete_journal_entry(
    id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    entry = db.query(TradeJournal).filter(
        TradeJournal.id == id,
        TradeJournal.user_id == current_user.id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    db.delete(entry)
    db.commit()
    return {"message": "Journal entry deleted"}

@router.get("/stats", response_model=JournalStatsOut)
def get_journal_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    entries = db.query(TradeJournal).filter(TradeJournal.user_id == current_user.id).all()
    
    total = len(entries)
    if total == 0:
        return JournalStatsOut(
            total_trades=0,
            wins=0,
            losses=0,
            breakeven=0,
            open_trades=0,
            win_rate=0.0,
            total_pnl=0.0,
            average_win=0.0,
            average_loss=0.0,
            profit_factor=0.0,
            best_trade=0.0,
            worst_trade=0.0
        )

    wins = [e.profit_loss for e in entries if e.profit_loss > 0]
    losses = [e.profit_loss for e in entries if e.profit_loss < 0]
    be_count = sum(1 for e in entries if e.outcome == "BREAKEVEN")
    open_count = sum(1 for e in entries if e.outcome == "OPEN")

    total_pnl = sum(e.profit_loss for e in entries)
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    
    win_rate = round((len(wins) / (len(wins) + len(losses))) * 100.0, 1) if (len(wins) + len(losses)) > 0 else 0.0
    avg_win = round(sum(wins) / len(wins), 2) if wins else 0.0
    avg_loss = round(sum(losses) / len(losses), 2) if losses else 0.0
    pf = round(gross_win / gross_loss, 2) if gross_loss > 0 else (gross_win if gross_win > 0 else 1.0)
    best_tr = max((e.profit_loss for e in entries), default=0.0)
    worst_tr = min((e.profit_loss for e in entries), default=0.0)

    return JournalStatsOut(
        total_trades=total,
        wins=len(wins),
        losses=len(losses),
        breakeven=be_count,
        open_trades=open_count,
        win_rate=win_rate,
        total_pnl=round(total_pnl, 2),
        average_win=avg_win,
        average_loss=avg_loss,
        profit_factor=pf,
        best_trade=round(best_tr, 2),
        worst_trade=round(worst_tr, 2)
    )
