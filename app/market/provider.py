from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

class MarketDataProvider(ABC):
    """
    Abstract Base Class for Market Data Providers (Mock, Binance, TwelveData, Yahoo, etc.)
    """

    @abstractmethod
    def get_latest_price(self, symbol: str) -> float:
        """Returns the latest market price for the given symbol."""
        pass

    @abstractmethod
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Returns 24h ticker data (price, change, high, low, volume, timestamp)."""
        pass

    @abstractmethod
    def get_all_tickers(self) -> List[Dict[str, Any]]:
        """Returns tickers for all supported market assets."""
        pass

    @abstractmethod
    def get_historical_candles(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Returns OHLCV candles sorted chronologically.
        Each candle dictionary contains: time (unix timestamp), open, high, low, close, volume.
        """
        pass
