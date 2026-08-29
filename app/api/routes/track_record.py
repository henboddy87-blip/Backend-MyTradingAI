from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.schemas import TrackRecordSummaryOut
from app.services.track_record_service import TrackRecordService

router = APIRouter(prefix="/track-record", tags=["Track Record"])

@router.get("/", response_model=TrackRecordSummaryOut)
def get_track_record(
    symbol: Optional[str] = Query(None),
    timeframe: Optional[str] = Query(None),
    min_confidence: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    return TrackRecordService.calculate_track_record(
        db,
        symbol=symbol,
        timeframe=timeframe,
        min_confidence=min_confidence
    )
