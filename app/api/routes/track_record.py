from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.schemas import TrackRecordSummaryOut
from app.services.track_record_service import TrackRecordService

router = APIRouter(prefix="/track-record", tags=["Track Record"])

@router.get("/", response_model=TrackRecordSummaryOut)
def get_track_record(db: Session = Depends(get_db)):
    return TrackRecordService.calculate_track_record(db)
