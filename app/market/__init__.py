from app.config import settings
from app.market.provider import MarketDataProvider
from app.market.mock_provider import MockMarketDataProvider

def get_market_data_provider() -> MarketDataProvider:
    provider_name = settings.MARKET_DATA_PROVIDER.lower()
    # In local/mock mode, return MockMarketDataProvider
    # Other real providers can be plugged in here
    return MockMarketDataProvider()

__all__ = ["MarketDataProvider", "MockMarketDataProvider", "get_market_data_provider"]
