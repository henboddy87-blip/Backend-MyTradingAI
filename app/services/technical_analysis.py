import math
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
from app.schemas.schemas import TechnicalAnalysisResult, MACDResult, BollingerBandsResult

class TechnicalAnalysisService:
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        if not prices or len(prices) < period:
            return prices[-1] if prices else 0.0
        k = 2.0 / (period + 1.0)
        ema = sum(prices[:period]) / period
        for price in prices[period:]:
            ema = (price * k) + (ema * (1.0 - k))
        return ema

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50.0
        gains, losses = [], []
        for i in range(1, len(prices)):
            diff = prices[i] - prices[i - 1]
            if diff >= 0:
                gains.append(diff)
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(abs(diff))
        
        # Initial average
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return round(rsi, 2)

    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal_period: int = 9) -> MACDResult:
        if len(prices) < slow + signal_period:
            return MACDResult(value=0.0, signal=0.0, histogram=0.0)
        
        # Calculate fast and slow EMAs across time
        k_fast = 2.0 / (fast + 1)
        k_slow = 2.0 / (slow + 1)
        
        fast_ema = sum(prices[:fast]) / fast
        slow_ema = sum(prices[:slow]) / slow
        
        macd_line = []
        for i, price in enumerate(prices):
            if i >= fast:
                fast_ema = (price * k_fast) + (fast_ema * (1 - k_fast))
            if i >= slow:
                slow_ema = (price * k_slow) + (slow_ema * (1 - k_slow))
                macd_line.append(fast_ema - slow_ema)
        
        if len(macd_line) < signal_period:
            val = macd_line[-1] if macd_line else 0.0
            return MACDResult(value=round(val, 4), signal=round(val, 4), histogram=0.0)

        # Signal line is EMA of macd_line
        k_sig = 2.0 / (signal_period + 1)
        sig_ema = sum(macd_line[:signal_period]) / signal_period
        for val in macd_line[signal_period:]:
            sig_ema = (val * k_sig) + (sig_ema * (1 - k_sig))

        macd_val = macd_line[-1]
        hist = macd_val - sig_ema
        return MACDResult(value=round(macd_val, 4), signal=round(sig_ema, 4), histogram=round(hist, 4))

    @staticmethod
    def calculate_atr(candles: List[Dict[str, Any]], period: int = 14) -> float:
        if len(candles) < 2:
            return 1.0
        trs = []
        for i in range(1, len(candles)):
            curr = candles[i]
            prev = candles[i - 1]
            tr = max(
                curr["high"] - curr["low"],
                abs(curr["high"] - prev["close"]),
                abs(curr["low"] - prev["close"])
            )
            trs.append(tr)
        
        if len(trs) < period:
            return round(sum(trs) / len(trs), 4) if trs else 1.0

        atr = sum(trs[:period]) / period
        for tr in trs[period:]:
            atr = (atr * (period - 1) + tr) / period
        return round(atr, 4)

    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, num_std: float = 2.0) -> BollingerBandsResult:
        if len(prices) < period:
            p = prices[-1] if prices else 0.0
            return BollingerBandsResult(upper=p, middle=p, lower=p)
        
        recent = prices[-period:]
        sma = sum(recent) / period
        variance = sum((x - sma) ** 2 for x in recent) / period
        std_dev = math.sqrt(variance)
        
        return BollingerBandsResult(
            upper=round(sma + (num_std * std_dev), 4),
            middle=round(sma, 4),
            lower=round(sma - (num_std * std_dev), 4)
        )

    @staticmethod
    def find_support_resistance(candles: List[Dict[str, Any]], window: int = 5) -> Tuple[List[float], List[float]]:
        if len(candles) < window * 2 + 1:
            return [], []
        
        supports, resistances = [], []
        for i in range(window, len(candles) - window):
            curr_low = candles[i]["low"]
            curr_high = candles[i]["high"]
            
            # Check swing low
            is_low = all(curr_low <= candles[i + j]["low"] for j in range(-window, window + 1) if j != 0)
            if is_low:
                supports.append(round(curr_low, 4))
                
            # Check swing high
            is_high = all(curr_high >= candles[i + j]["high"] for j in range(-window, window + 1) if j != 0)
            if is_high:
                resistances.append(round(curr_high, 4))

        # Return unique recent levels
        recent_supports = sorted(list(set(supports[-3:]))) if supports else []
        recent_resistances = sorted(list(set(resistances[-3:]))) if resistances else []
        return recent_supports, recent_resistances

    @classmethod
    def analyze(cls, symbol: str, timeframe: str, candles: List[Dict[str, Any]]) -> TechnicalAnalysisResult:
        if not candles:
            return TechnicalAnalysisResult(
                symbol=symbol,
                timeframe=timeframe,
                trend="neutral",
                momentum="moderate",
                rsi=50.0,
                macd=MACDResult(value=0, signal=0, histogram=0),
                ema_20=0, ema_50=0, ema_200=0,
                atr=1.0,
                bollinger_bands=BollingerBandsResult(upper=0, middle=0, lower=0),
                support_levels=[],
                resistance_levels=[],
                summary="Insufficient data for analysis",
                timestamp=datetime.now(timezone.utc)
            )

        closes = [c["close"] for c in candles]
        current_close = closes[-1]

        rsi = cls.calculate_rsi(closes, period=14)
        macd = cls.calculate_macd(closes)
        ema_20 = round(cls.calculate_ema(closes, 20), 4)
        ema_50 = round(cls.calculate_ema(closes, 50), 4)
        ema_200 = round(cls.calculate_ema(closes, 200 if len(closes) >= 200 else len(closes)), 4)
        atr = cls.calculate_atr(candles, 14)
        bb = cls.calculate_bollinger_bands(closes, 20)
        supports, resistances = cls.find_support_resistance(candles)

        # Trend Determination
        if current_close > ema_20 > ema_50 and rsi > 52:
            trend = "bullish"
        elif current_close < ema_20 < ema_50 and rsi < 48:
            trend = "bearish"
        else:
            trend = "neutral"

        # Momentum Determination
        if abs(macd.histogram) > (atr * 0.2) or rsi > 65 or rsi < 35:
            momentum = "strong"
        elif abs(macd.histogram) > (atr * 0.05):
            momentum = "moderate"
        else:
            momentum = "weak"

        summary = f"{trend.upper()} structure on {timeframe}. RSI is at {rsi}, MACD histogram is {macd.histogram:+.4f}. EMA 20/50 alignment: {'Bullish' if ema_20 > ema_50 else 'Bearish'}."

        return TechnicalAnalysisResult(
            symbol=symbol,
            timeframe=timeframe,
            trend=trend,
            momentum=momentum,
            rsi=rsi,
            macd=macd,
            ema_20=ema_20,
            ema_50=ema_50,
            ema_200=ema_200,
            atr=atr,
            bollinger_bands=bb,
            support_levels=supports,
            resistance_levels=resistances,
            summary=summary,
            timestamp=datetime.now(timezone.utc)
        )
