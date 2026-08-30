import math
import time
import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from app.market.provider import MarketDataProvider

# Base reference configurations for supported assets
BASE_ASSETS = {
    "XAUUSD": {"name": "Gold / US Dollar", "type": "commodity", "base_price": 4466.00, "volatility": 0.006, "precision": 2},
    "BTCUSDT": {"name": "Bitcoin / Tether", "type": "crypto", "base_price": 78680.00, "volatility": 0.015, "precision": 2},
    "ETHUSDT": {"name": "Ethereum / Tether", "type": "crypto", "base_price": 2465.00, "volatility": 0.018, "precision": 2},
    "SOLUSDT": {"name": "Solana / Tether", "type": "crypto", "base_price": 106.00, "volatility": 0.025, "precision": 2},
    "BNBUSDT": {"name": "BNB / Tether", "type": "crypto", "base_price": 695.50, "volatility": 0.012, "precision": 2},
    "EURUSD": {"name": "Euro / US Dollar", "type": "forex", "base_price": 1.1585, "volatility": 0.003, "precision": 4},
    "GBPUSD": {"name": "British Pound / US Dollar", "type": "forex", "base_price": 1.3530, "volatility": 0.004, "precision": 4},
    "USDJPY": {"name": "US Dollar / Japanese Yen", "type": "forex", "base_price": 155.20, "volatility": 0.004, "precision": 2},
    "USOIL": {"name": "Crude Oil WTI", "type": "commodity", "base_price": 83.40, "volatility": 0.012, "precision": 2},
    "UKOIL": {"name": "Brent Crude Oil", "type": "commodity", "base_price": 87.20, "volatility": 0.011, "precision": 2},
    "AAPL": {"name": "Apple Inc.", "type": "stock", "base_price": 234.50, "volatility": 0.008, "precision": 2},
    "TSLA": {"name": "Tesla, Inc.", "type": "stock", "base_price": 258.00, "volatility": 0.020, "precision": 2},
    "NVDA": {"name": "NVIDIA Corporation", "type": "stock", "base_price": 217.50, "volatility": 0.022, "precision": 2},
    "NAS100": {"name": "Nasdaq 100", "type": "index", "base_price": 29490.00, "volatility": 0.007, "precision": 2},
    "US30": {"name": "Dow Jones 30", "type": "index", "base_price": 44250.00, "volatility": 0.005, "precision": 2},
}

TIMEFRAME_SECONDS = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
}

class MockMarketDataProvider(MarketDataProvider):
    def __init__(self):
        self.assets = BASE_ASSETS

    def _get_synthetic_multiplier(self, symbol: str, timestamp_sec: int) -> float:
        """
        Deterministic wave equation combining multiple sinusoidal frequencies + hash offset
        Produces consistent, organic looking trends, swings, and pullbacks across time.
        """
        symbol_hash = sum(ord(c) for c in symbol) * 100
        t = (timestamp_sec + symbol_hash) / 3600.0 # Time in hours
        
        # Primary macro cycle (~48h), medium swing (~12h), micro oscillations (~2h, 30m)
        w1 = math.sin(t / 48.0 * 2 * math.pi) * 0.04
        w2 = math.cos(t / 12.0 * 2 * math.pi) * 0.02
        w3 = math.sin(t / 2.5 * 2 * math.pi) * 0.008
        w4 = math.cos(t / 0.5 * 2 * math.pi) * 0.003
        
        return 1.0 + (w1 + w2 + w3 + w4)

    def get_latest_price(self, symbol: str) -> float:
        symbol = symbol.upper()
        asset = self.assets.get(symbol, {"base_price": 100.0, "precision": 2})
        now_sec = int(time.time())
        multiplier = self._get_synthetic_multiplier(symbol, now_sec)
        price = asset["base_price"] * multiplier
        return round(price, asset.get("precision", 2))

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        symbol = symbol.upper()
        asset = self.assets.get(symbol, {
            "name": symbol,
            "type": "crypto",
            "base_price": 100.0,
            "volatility": 0.01,
            "precision": 2
        })
        now_sec = int(time.time())
        current_price = self.get_latest_price(symbol)
        
        # Price 24 hours ago
        day_ago_sec = now_sec - 86400
        day_ago_mult = self._get_synthetic_multiplier(symbol, day_ago_sec)
        open_24h = asset["base_price"] * day_ago_mult
        
        change_pct = ((current_price - open_24h) / open_24h) * 100.0
        direction = "up" if change_pct >= 0 else "down"
        
        high_24h = current_price * 1.025 if change_pct > 0 else open_24h * 1.015
        low_24h = open_24h * 0.98 if change_pct > 0 else current_price * 0.975
        volume_24h = round(asset["base_price"] * 1450.0, 2)

        return {
            "symbol": symbol,
            "name": asset["name"],
            "market_type": asset["type"],
            "price": current_price,
            "change_24h": round(change_pct, 2),
            "direction": direction,
            "high_24h": round(high_24h, asset["precision"]),
            "low_24h": round(low_24h, asset["precision"]),
            "volume_24h": volume_24h,
            "timestamp": datetime.now(timezone.utc),
            "market_status": "open"
        }

    def get_all_tickers(self) -> List[Dict[str, Any]]:
        tickers = []
        for symbol in self.assets.keys():
            tickers.append(self.get_ticker(symbol))
        return tickers

    def get_historical_candles(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> List[Dict[str, Any]]:
        symbol = symbol.upper()
        asset = self.assets.get(symbol, {
            "name": symbol,
            "type": "crypto",
            "base_price": 100.0,
            "volatility": 0.01,
            "precision": 2
        })
        
        step_seconds = TIMEFRAME_SECONDS.get(timeframe, 3600)
        now_sec = int(time.time())
        # Align to candle boundary
        current_candle_time = (now_sec // step_seconds) * step_seconds
        
        candles = []
        precision = asset.get("precision", 2)
        base_price = asset["base_price"]
        vol = asset.get("volatility", 0.01)

        start_time = current_candle_time - (limit * step_seconds)
        
        prev_close = base_price * self._get_synthetic_multiplier(symbol, start_time)

        for i in range(limit):
            candle_time = start_time + (i * step_seconds)
            open_price = prev_close
            
            # Deterministic pseudo-random variation based on timestamp and symbol
            rnd_seed = (candle_time + sum(ord(c) for c in symbol)) % 10000
            noise = (math.sin(rnd_seed) * 0.5 + math.cos(rnd_seed * 1.3) * 0.5) * vol * base_price * 0.4
            
            wave_mult = self._get_synthetic_multiplier(symbol, candle_time + step_seconds)
            target_close = base_price * wave_mult + noise
            
            close_price = round(target_close, precision)
            high_price = round(max(open_price, close_price) + abs(noise) * 0.8 + (base_price * vol * 0.15), precision)
            low_price = round(min(open_price, close_price) - abs(noise) * 0.8 - (base_price * vol * 0.15), precision)
            
            # Ensure high and low bound open and close
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)
            
            volume = round(abs(close_price - open_price) * 1200.0 + 5000.0, 2)
            
            candles.append({
                "time": candle_time,
                "open": round(open_price, precision),
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume
            })
            
            prev_close = close_price

        return candles
