from app.config import settings
from app.market.provider import MarketDataProvider
from app.market.mock_provider import MockMarketDataProvider
from app.market.live_provider import LiveMarketDataProvider

_live_provider_instance = None
_mock_provider_instance = None

def get_market_data_provider() -> MarketDataProvider:
    global _live_provider_instance, _mock_provider_instance
    provider_name = settings.MARKET_DATA_PROVIDER.lower()
    if provider_name == "mock":
        if _mock_provider_instance is None:
            _mock_provider_instance = MockMarketDataProvider()
        return _mock_provider_instance
    
    # Default to live market data provider (Binance + Yahoo Finance)
    if _live_provider_instance is None:
        _live_provider_instance = LiveMarketDataProvider()
    return _live_provider_instance

__all__ = ["MarketDataProvider", "MockMarketDataProvider", "LiveMarketDataProvider", "get_market_data_provider"]

