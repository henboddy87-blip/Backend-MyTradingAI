from fastapi import APIRouter, Query
from app.market import get_market_data_provider
from app.services.technical_analysis import TechnicalAnalysisService
from app.schemas.schemas import TechnicalAnalysisResult

router = APIRouter(prefix="/technical", tags=["Technical Analysis"])

@router.get("/analyze/{symbol}", response_model=TechnicalAnalysisResult)
def analyze_asset(
    symbol: str,
    timeframe: str = Query("1h", regex="^(1m|5m|15m|30m|1h|4h|1d)$"),
    limit: int = Query(120, ge=30, le=300)
):
    provider = get_market_data_provider()
    candles = provider.get_historical_candles(symbol.upper(), timeframe=timeframe, limit=limit)
    return TechnicalAnalysisService.analyze(symbol.upper(), timeframe, candles)
