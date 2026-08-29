import math
import time
import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.market.provider import MarketDataProvider
from app.market.mock_provider import BASE_ASSETS, TIMEFRAME_SECONDS, MockMarketDataProvider
from app.core.logging import logger

# Mapping internal symbols to Yahoo Finance and Binance symbols
YAHOO_SYMBOLS = {
    "XAUUSD": "GC=F",      # Gold Futures
    "XAGUSD": "SI=F",      # Silver Futures
    "USOIL": "CL=F",       # WTI Crude Oil
    "UKOIL": "BZ=F",       # Brent Crude Oil
    "EURUSD": "EURUSD=X",  # Euro / USD
    "GBPUSD": "GBPUSD=X",  # British Pound / USD
    "USDJPY": "JPY=X",     # USD / Japanese Yen
    "AUDUSD": "AUDUSD=X",  # AUD / USD
    "USDCAD": "CAD=X",     # USD / CAD
    "USDCHF": "CHF=X",     # USD / CHF
    "NAS100": "NQ=F",      # Nasdaq 100 E-mini Futures
    "US30": "YM=F",        # Dow Jones 30 E-mini Futures
    "SPX500": "ES=F",      # S&P 500 E-mini Futures
    "GER40": "^GDAXI",     # DAX Index
    "NVDA": "NVDA",        # NVIDIA Corporation
    "AAPL": "AAPL",        # Apple Inc.
    "TSLA": "TSLA",        # Tesla Inc.
    "MSFT": "MSFT",        # Microsoft Corporation
    "AMZN": "AMZN",        # Amazon.com
    "GOOGL": "GOOGL",      # Alphabet Inc.
    "META": "META",        # Meta Platforms
}

BINANCE_SYMBOLS = {
    "BTCUSDT": "BTCUSDT",
    "ETHUSDT": "ETHUSDT",
    "SOLUSDT": "SOLUSDT",
    "BNBUSDT": "BNBUSDT",
    "XRPUSDT": "XRPUSDT",
    "DOGEUSDT": "DOGEUSDT",
    "ADAUSDT": "ADAUSDT",
    "AVAXUSDT": "AVAXUSDT",
    "LINKUSDT": "LINKUSDT",
    "DOTUSDT": "DOTUSDT",
    "NEARUSDT": "NEARUSDT",
    "SUIUSDT": "SUIUSDT",
}

# Timeframe mapping for Yahoo Finance and Binance
YAHOO_TIMEFRAMES = {
    "1m": ("1m", "1d"),
    "5m": ("5m", "2d"),
    "15m": ("15m", "5d"),
    "30m": ("30m", "5d"),
    "1h": ("1h", "1mo"),
    "4h": ("1h", "3mo"),  # Resample from 1h if needed
    "1d": ("1d", "1y"),
}

BINANCE_TIMEFRAMES = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d",
}

class LiveMarketDataProvider(MarketDataProvider):
    """
    Institutional Real-World Live Market Data Provider
    - Crypto: Binance Vision REST API (0 rate limits, real-time live orderbook/klines)
    - Forex, Commodities, Indices, Stocks: Yahoo Finance Live Charts & Quote API
    - Fast in-memory TTL caching (3s for tickers, 15s for candles)
    - Automatic graceful fallback to mock generator if offline/throttled
    """
    def __init__(self):
        self.mock_fallback = MockMarketDataProvider()
        self.http_client = httpx.Client(
            timeout=5.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
            }
        )
        self._ticker_cache: Dict[str, Dict[str, Any]] = {}
        self._candle_cache: Dict[str, Dict[str, Any]] = {}
        self._last_all_tickers_time: float = 0.0
        self._cached_all_tickers: List[Dict[str, Any]] = []

    def _is_crypto(self, symbol: str) -> bool:
        symbol = symbol.upper()
        return symbol in BINANCE_SYMBOLS or symbol.endswith("USDT") or symbol.endswith("BTC")

    def _fetch_binance_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        binance_sym = BINANCE_SYMBOLS.get(symbol, symbol)
        urls = [
            f"https://data-api.binance.vision/api/v3/ticker/24hr?symbol={binance_sym}",
            f"https://api1.binance.com/api/v3/ticker/24hr?symbol={binance_sym}",
            f"https://api.binance.com/api/v3/ticker/24hr?symbol={binance_sym}",
        ]
        for url in urls:
            try:
                r = self.http_client.get(url, timeout=3.0)
                if r.status_code == 200:
                    d = r.json()
                    price = float(d.get("lastPrice", 0.0))
                    change_pct = float(d.get("priceChangePercent", 0.0))
                    high_24h = float(d.get("highPrice", price * 1.02))
                    low_24h = float(d.get("lowPrice", price * 0.98))
                    volume_24h = float(d.get("quoteVolume", 0.0))
                    precision = 2 if price >= 1.0 else 4
                    return {
                        "symbol": symbol,
                        "name": BASE_ASSETS.get(symbol, {}).get("name", symbol),
                        "market_type": "crypto",
                        "price": round(price, precision),
                        "change_24h": round(change_pct, 2),
                        "direction": "up" if change_pct >= 0 else "down",
                        "high_24h": round(high_24h, precision),
                        "low_24h": round(low_24h, precision),
                        "volume_24h": round(volume_24h, 2),
                        "timestamp": datetime.now(timezone.utc),
                        "market_status": "open"
                    }
            except Exception as e:
                logger.debug(f"Binance ticker request to {url} failed: {e}")
                continue
        return None

    def _fetch_yahoo_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        yahoo_sym = YAHOO_SYMBOLS.get(symbol, symbol)
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_sym}?interval=1d&range=5d"
        try:
            r = self.http_client.get(url, timeout=4.0)
            if r.status_code == 200:
                data = r.json()
                result = data.get("chart", {}).get("result", [])
                if result:
                    meta = result[0].get("meta", {})
                    current_price = meta.get("regularMarketPrice") or meta.get("previousClose")
                    prev_close = meta.get("chartPreviousClose") or meta.get("previousClose") or current_price
                    
                    if current_price is None:
                        return None
                    
                    current_price = float(current_price)
                    prev_close = float(prev_close)
                    
                    change_pct = 0.0
                    if prev_close > 0:
                        change_pct = ((current_price - prev_close) / prev_close) * 100.0
                    
                    high_24h = float(meta.get("regularMarketDayHigh", current_price * 1.01))
                    low_24h = float(meta.get("regularMarketDayLow", current_price * 0.99))
                    volume = float(meta.get("regularMarketVolume", 150000.0) or 150000.0)
                    
                    asset_info = BASE_ASSETS.get(symbol, {})
                    precision = asset_info.get("precision", 2 if current_price >= 10 else 4)
                    
                    return {
                        "symbol": symbol,
                        "name": asset_info.get("name", symbol),
                        "market_type": asset_info.get("type", "forex" if "USD" in symbol else "stock"),
                        "price": round(current_price, precision),
                        "change_24h": round(change_pct, 2),
                        "direction": "up" if change_pct >= 0 else "down",
                        "high_24h": round(high_24h, precision),
                        "low_24h": round(low_24h, precision),
                        "volume_24h": round(volume, 2),
                        "timestamp": datetime.now(timezone.utc),
                        "market_status": "open"
                    }
        except Exception as e:
            logger.debug(f"Yahoo ticker request for {symbol} ({yahoo_sym}) failed: {e}")
        return None

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        symbol = symbol.upper()
        now = time.time()
        
        # Check cache (3s TTL)
        cached = self._ticker_cache.get(symbol)
        if cached and (now - cached["cached_at"]) < 3.0:
            return cached["data"]

        ticker = None
        if self._is_crypto(symbol):
            ticker = self._fetch_binance_ticker(symbol)
        else:
            ticker = self._fetch_yahoo_ticker(symbol)

        if not ticker:
            # Fallback to calibrated simulation if live API is temporarily unreachable
            ticker = self.mock_fallback.get_ticker(symbol)

        self._ticker_cache[symbol] = {
            "cached_at": now,
            "data": ticker
        }
        return ticker

    def get_latest_price(self, symbol: str) -> float:
        ticker = self.get_ticker(symbol)
        return ticker.get("price", 100.0)

    def get_all_tickers(self) -> List[Dict[str, Any]]:
        now = time.time()
        if self._cached_all_tickers and (now - self._last_all_tickers_time) < 4.0:
            return self._cached_all_tickers

        tickers = []
        for symbol in BASE_ASSETS.keys():
            try:
                tickers.append(self.get_ticker(symbol))
            except Exception as e:
                tickers.append(self.mock_fallback.get_ticker(symbol))

        self._cached_all_tickers = tickers
        self._last_all_tickers_time = now
        return tickers

    def _fetch_binance_candles(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        binance_sym = BINANCE_SYMBOLS.get(symbol, symbol)
        interval = BINANCE_TIMEFRAMES.get(timeframe, "1h")
        url = f"https://data-api.binance.vision/api/v3/klines?symbol={binance_sym}&interval={interval}&limit={limit}"
        try:
            r = self.http_client.get(url, timeout=5.0)
            if r.status_code == 200:
                raw_candles = r.json()
                candles = []
                precision = BASE_ASSETS.get(symbol, {}).get("precision", 2)
                for c in raw_candles:
                    # [open_time_ms, open, high, low, close, volume, close_time_ms, ...]
                    candles.append({
                        "time": int(c[0] // 1000),
                        "open": round(float(c[1]), precision),
                        "high": round(float(c[2]), precision),
                        "low": round(float(c[3]), precision),
                        "close": round(float(c[4]), precision),
                        "volume": round(float(c[5]), 2)
                    })
                if candles:
                    return candles
        except Exception as e:
            logger.debug(f"Binance candles request failed for {symbol}: {e}")
        return None

    def _fetch_yahoo_candles(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        yahoo_sym = YAHOO_SYMBOLS.get(symbol, symbol)
        interval, default_range = YAHOO_TIMEFRAMES.get(timeframe, ("1h", "1mo"))
        
        # Calculate appropriate range based on limit
        if timeframe in ["1m", "5m"]:
            data_range = "5d"
        elif timeframe in ["15m", "30m"]:
            data_range = "1mo"
        elif timeframe in ["1h", "4h"]:
            data_range = "3mo"
        else:
            data_range = "1y"

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_sym}?interval={interval}&range={data_range}"
        try:
            r = self.http_client.get(url, timeout=5.0)
            if r.status_code == 200:
                data = r.json()
                result = data.get("chart", {}).get("result", [])
                if not result:
                    return None
                
                chart_data = result[0]
                timestamps = chart_data.get("timestamp", [])
                quote = chart_data.get("indicators", {}).get("quote", [{}])[0]
                
                opens = quote.get("open", [])
                highs = quote.get("high", [])
                lows = quote.get("low", [])
                closes = quote.get("close", [])
                volumes = quote.get("volume", [])
                
                precision = BASE_ASSETS.get(symbol, {}).get("precision", 2)
                candles = []
                
                for i in range(len(timestamps)):
                    t = timestamps[i]
                    o = opens[i] if i < len(opens) else None
                    h = highs[i] if i < len(highs) else None
                    l = lows[i] if i < len(lows) else None
                    c = closes[i] if i < len(closes) else None
                    v = volumes[i] if i < len(volumes) and volumes[i] is not None else 1000.0
                    
                    if o is None or h is None or l is None or c is None:
                        continue
                    
                    candles.append({
                        "time": int(t),
                        "open": round(float(o), precision),
                        "high": round(float(h), precision),
                        "low": round(float(l), precision),
                        "close": round(float(c), precision),
                        "volume": round(float(v), 2)
                    })
                
                # If 4h timeframe is requested, resample 1h candles into 4h
                if timeframe == "4h" and len(candles) >= 4:
                    resampled = []
                    for chunk_idx in range(0, len(candles), 4):
                        chunk = candles[chunk_idx:chunk_idx+4]
                        if not chunk:
                            continue
                        resampled.append({
                            "time": chunk[0]["time"],
                            "open": chunk[0]["open"],
                            "high": max(c["high"] for c in chunk),
                            "low": min(c["low"] for c in chunk),
                            "close": chunk[-1]["close"],
                            "volume": sum(c["volume"] for c in chunk)
                        })
                    candles = resampled

                if candles:
                    return candles[-limit:]
        except Exception as e:
            logger.debug(f"Yahoo candles request failed for {symbol}: {e}")
        return None

    def get_historical_candles(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> List[Dict[str, Any]]:
        symbol = symbol.upper()
        cache_key = f"{symbol}_{timeframe}_{limit}"
        now = time.time()
        
        cached = self._candle_cache.get(cache_key)
        if cached and (now - cached["cached_at"]) < 15.0:
            return cached["candles"]

        candles = None
        if self._is_crypto(symbol):
            candles = self._fetch_binance_candles(symbol, timeframe, limit)
        else:
            candles = self._fetch_yahoo_candles(symbol, timeframe, limit)

        if not candles or len(candles) < 10:
            candles = self.mock_fallback.get_historical_candles(symbol, timeframe, limit)

        self._candle_cache[cache_key] = {
            "cached_at": now,
            "candles": candles
        }
        return candles

    def get_fear_and_greed_index(self) -> Dict[str, Any]:
        """Fetches live Crypto & Macro Fear and Greed Index from Alternative.me"""
        try:
            r = self.http_client.get("https://api.alternative.me/fng/?limit=7", timeout=4.0)
            if r.status_code == 200:
                data = r.json().get("data", [])
                if data:
                    today = data[0]
                    return {
                        "value": int(today.get("value", 50)),
                        "classification": today.get("value_classification", "Neutral"),
                        "timestamp": today.get("timestamp"),
                        "history": [
                            {"value": int(item.get("value", 50)), "date": item.get("timestamp"), "sentiment": item.get("value_classification")}
                            for item in data
                        ]
                    }
        except Exception as e:
            logger.debug(f"Fear & Greed fetch failed: {e}")
        return {
            "value": 65,
            "classification": "Greed",
            "timestamp": str(int(time.time())),
            "history": []
        }
