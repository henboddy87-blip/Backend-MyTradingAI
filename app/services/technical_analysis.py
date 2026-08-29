import math
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone
from app.schemas.schemas import (
    TechnicalAnalysisResult, MACDResult, BollingerBandsResult,
    MarketStructureResult, MarketRegimeResult, MultiTimeframeSummary,
    TimeframeAlignment, ConfidenceScoreBreakdown, SignalInvalidation
)

class TechnicalAnalysisService:
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        if not prices or len(prices) < period:
            return prices[-1] if prices else 0.0
        k = 2.0 / (period + 1.0)
        ema = sum(prices[:period]) / period
        for price in prices[period:]:
            ema = (price * k) + (ema * (1.0 - k))
        return round(ema, 4)

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
    def calculate_adx(candles: List[Dict[str, Any]], period: int = 14) -> float:
        """Calculates Average Directional Index (ADX) for trend strength"""
        if len(candles) < period * 2:
            return 25.0
        
        plus_dm, minus_dm, trs = [], [], []
        for i in range(1, len(candles)):
            curr = candles[i]
            prev = candles[i - 1]
            
            up_move = curr["high"] - prev["high"]
            down_move = prev["low"] - curr["low"]
            
            plus_dm.append(up_move if (up_move > down_move and up_move > 0) else 0.0)
            minus_dm.append(down_move if (down_move > up_move and down_move > 0) else 0.0)
            
            tr = max(
                curr["high"] - curr["low"],
                abs(curr["high"] - prev["close"]),
                abs(curr["low"] - prev["close"])
            )
            trs.append(tr)
        
        smoothed_tr = sum(trs[:period])
        smoothed_pdm = sum(plus_dm[:period])
        smoothed_mdm = sum(minus_dm[:period])
        
        dx_list = []
        for i in range(period, len(trs)):
            smoothed_tr = smoothed_tr - (smoothed_tr / period) + trs[i]
            smoothed_pdm = smoothed_pdm - (smoothed_pdm / period) + plus_dm[i]
            smoothed_mdm = smoothed_mdm - (smoothed_mdm / period) + minus_dm[i]
            
            pdi = (smoothed_pdm / smoothed_tr * 100) if smoothed_tr > 0 else 0
            mdi = (smoothed_mdm / smoothed_tr * 100) if smoothed_tr > 0 else 0
            
            dx = (abs(pdi - mdi) / (pdi + mdi) * 100) if (pdi + mdi) > 0 else 0
            dx_list.append(dx)
        
        if not dx_list:
            return 25.0
        adx = sum(dx_list[-period:]) / min(len(dx_list), period)
        return round(adx, 2)

    @staticmethod
    def calculate_stochastic(candles: List[Dict[str, Any]], k_period: int = 14, d_period: int = 3) -> Tuple[float, float]:
        """Calculates Fast Stochastic %K and %D"""
        if len(candles) < k_period + d_period:
            return 50.0, 50.0
        
        k_values = []
        for i in range(k_period, len(candles) + 1):
            window = candles[i - k_period:i]
            current_close = window[-1]["close"]
            highest_high = max(c["high"] for c in window)
            lowest_low = min(c["low"] for c in window)
            
            if highest_high == lowest_low:
                k_values.append(50.0)
            else:
                k = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100.0
                k_values.append(k)
        
        if not k_values:
            return 50.0, 50.0
        
        current_k = k_values[-1]
        current_d = sum(k_values[-d_period:]) / min(len(k_values), d_period)
        return round(current_k, 2), round(current_d, 2)

    @staticmethod
    def find_support_resistance(candles: List[Dict[str, Any]], window: int = 5) -> Tuple[List[float], List[float]]:
        if len(candles) < window * 2 + 1:
            return [], []
        
        supports, resistances = [], []
        for i in range(window, len(candles) - window):
            curr_low = candles[i]["low"]
            curr_high = candles[i]["high"]
            
            is_low = all(curr_low <= candles[i + j]["low"] for j in range(-window, window + 1) if j != 0)
            if is_low:
                supports.append(round(curr_low, 4))
                
            is_high = all(curr_high >= candles[i + j]["high"] for j in range(-window, window + 1) if j != 0)
            if is_high:
                resistances.append(round(curr_high, 4))

        recent_supports = sorted(list(set(supports[-4:]))) if supports else []
        recent_resistances = sorted(list(set(resistances[-4:]))) if resistances else []
        return recent_supports, recent_resistances

    @classmethod
    def detect_market_structure(cls, candles: List[Dict[str, Any]], window: int = 4) -> MarketStructureResult:
        """
        Detects Institutional Market Structure:
        - Swing Highs & Swing Lows
        - Higher Highs (HH) & Higher Lows (HL) vs Lower Highs (LH) & Lower Lows (LL)
        - Break of Structure (BOS)
        - Change of Character (CHoCH)
        """
        if len(candles) < window * 2 + 3:
            return MarketStructureResult(
                structure_bias="RANGING",
                pattern="Consolidation / Range",
                break_of_structure=False,
                change_of_character=False,
                swing_highs=[],
                swing_lows=[]
            )

        swing_highs, swing_lows = [], []
        for i in range(window, len(candles) - window):
            curr_high = candles[i]["high"]
            curr_low = candles[i]["low"]
            
            if all(curr_high >= candles[i + j]["high"] for j in range(-window, window + 1) if j != 0):
                swing_highs.append(round(curr_high, 4))
            if all(curr_low <= candles[i + j]["low"] for j in range(-window, window + 1) if j != 0):
                swing_lows.append(round(curr_low, 4))

        current_close = candles[-1]["close"]
        
        # Analyze structure progression
        is_bullish_progression = False
        is_bearish_progression = False
        bos = False
        choch = False
        recent_bos = None
        recent_choch = None

        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            hh = swing_highs[-1] > swing_highs[-2]
            hl = swing_lows[-1] > swing_lows[-2]
            lh = swing_highs[-1] < swing_highs[-2]
            ll = swing_lows[-1] < swing_lows[-2]

            if hh and hl:
                is_bullish_progression = True
                pattern = "HH-HL (Bullish Trend Structure)"
                structure_bias = "BULLISH"
                if current_close > swing_highs[-1]:
                    bos = True
                    recent_bos = swing_highs[-1]
            elif lh and ll:
                is_bearish_progression = True
                pattern = "LH-LL (Bearish Trend Structure)"
                structure_bias = "BEARISH"
                if current_close < swing_lows[-1]:
                    bos = True
                    recent_bos = swing_lows[-1]
            elif hh and not hl:
                # Potential Change of Character from bearish to bullish
                pattern = "CHoCH (Bullish Reversal Shift)"
                structure_bias = "BULLISH"
                choch = True
                recent_choch = swing_highs[-2]
            elif ll and not lh:
                # Potential Change of Character from bullish to bearish
                pattern = "CHoCH (Bearish Reversal Shift)"
                structure_bias = "BEARISH"
                choch = True
                recent_choch = swing_lows[-2]
            else:
                pattern = "Range / Sideways Accumulation"
                structure_bias = "RANGING"
        else:
            pattern = "Building Structure Baseline"
            structure_bias = "RANGING"

        return MarketStructureResult(
            structure_bias=structure_bias,
            pattern=pattern,
            break_of_structure=bos,
            change_of_character=choch,
            swing_highs=swing_highs[-3:],
            swing_lows=swing_lows[-3:],
            recent_bos_level=recent_bos,
            recent_choch_level=recent_choch
        )

    @classmethod
    def detect_market_regime(
        cls,
        candles: List[Dict[str, Any]],
        current_close: float,
        ema_20: float,
        ema_50: float,
        ema_200: float,
        rsi: float,
        atr: float,
        adx: float,
        bb: BollingerBandsResult,
        structure: MarketStructureResult
    ) -> MarketRegimeResult:
        """
        Classifies Market Regime:
        - STRONG_TREND: High ADX (>25), clear EMA stacking, structure alignment
        - WEAK_TREND: Mild slope, ADX 18-25
        - RANGE: ADX < 18, price oscillating near BB middle
        - BREAKOUT: Price piercing BB bands with expansion
        - PULLBACK: Trend intact but short-term counter-move to EMA 20/50 support
        - HIGH_VOLATILITY: ATR expansion or extreme BB width
        - UNCERTAIN: Conflicting signals, no clear direction
        """
        bb_width = ((bb.upper - bb.lower) / bb.middle) if bb.middle > 0 else 0.0

        # Check Breakout
        if current_close > bb.upper or current_close < bb.lower:
            regime = "BREAKOUT"
            confidence = 88.0
            volatility_state = "EXPANDING"
            rec = "Wait for breakout confirmation or first retest before entry."
        # Check Strong Trend
        elif adx >= 28 and ((current_close > ema_20 > ema_50) or (current_close < ema_20 < ema_50)):
            regime = "STRONG_TREND"
            confidence = 92.0
            volatility_state = "NORMAL"
            rec = "Trade trend continuation pullbacks with directional momentum."
        # Check Pullback
        elif structure.structure_bias == "BULLISH" and current_close <= ema_20 and current_close >= ema_50:
            regime = "PULLBACK"
            confidence = 86.0
            volatility_state = "COMPRESSING"
            rec = "Look for bullish reaction wick off dynamic EMA 20/50 support."
        elif structure.structure_bias == "BEARISH" and current_close >= ema_20 and current_close <= ema_50:
            regime = "PULLBACK"
            confidence = 86.0
            volatility_state = "COMPRESSING"
            rec = "Look for bearish rejection off dynamic EMA 20/50 resistance."
        # Check Range
        elif adx < 20 or structure.structure_bias == "RANGING":
            regime = "RANGE"
            confidence = 80.0
            volatility_state = "COMPRESSING"
            rec = "Fade range extremes at verified Support & Resistance boundaries."
        # Check High Volatility
        elif bb_width > 0.04:
            regime = "HIGH_VOLATILITY"
            confidence = 75.0
            volatility_state = "EXPANDING"
            rec = "Widen stop loss parameters and reduce position sizing."
        else:
            regime = "WEAK_TREND"
            confidence = 70.0
            volatility_state = "NORMAL"
            rec = "Exercise patience for higher-timeframe confluence."

        return MarketRegimeResult(
            regime=regime,
            confidence=confidence,
            volatility_state=volatility_state,
            recommendation=rec
        )

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
                adx=25.0,
                stochastic_k=50.0,
                stochastic_d=50.0,
                bollinger_bands=BollingerBandsResult(upper=0, middle=0, lower=0),
                support_levels=[],
                resistance_levels=[],
                market_structure=None,
                market_regime=None,
                summary="Insufficient candle data for quantitative scan.",
                timestamp=datetime.now(timezone.utc)
            )

        closes = [c["close"] for c in candles]
        current_close = closes[-1]

        rsi = cls.calculate_rsi(closes, period=14)
        macd = cls.calculate_macd(closes)
        ema_20 = cls.calculate_ema(closes, 20)
        ema_50 = cls.calculate_ema(closes, 50)
        ema_200 = cls.calculate_ema(closes, 200 if len(closes) >= 200 else len(closes))
        atr = cls.calculate_atr(candles, 14)
        adx = cls.calculate_adx(candles, 14)
        stoch_k, stoch_d = cls.calculate_stochastic(candles, 14, 3)
        bb = cls.calculate_bollinger_bands(closes, 20)
        supports, resistances = cls.find_support_resistance(candles)
        structure = cls.detect_market_structure(candles)
        regime = cls.detect_market_regime(
            candles, current_close, ema_20, ema_50, ema_200, rsi, atr, adx, bb, structure
        )

        # Trend Determination
        if current_close > ema_20 > ema_50 and rsi > 52:
            trend = "bullish"
        elif current_close < ema_20 < ema_50 and rsi < 48:
            trend = "bearish"
        else:
            trend = "neutral"

        # Momentum Determination
        if abs(macd.histogram) > (atr * 0.15) or rsi > 65 or rsi < 35 or adx > 30:
            momentum = "strong"
        elif abs(macd.histogram) > (atr * 0.04):
            momentum = "moderate"
        else:
            momentum = "weak"

        summary = (
            f"{trend.upper()} bias on {timeframe} ({structure.pattern}). "
            f"RSI: {rsi}, ADX: {adx} ({regime.regime.replace('_', ' ')}). "
            f"EMA 20/50 alignment: {'Bullish' if ema_20 > ema_50 else 'Bearish'}."
        )

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
            adx=adx,
            stochastic_k=stoch_k,
            stochastic_d=stoch_d,
            bollinger_bands=bb,
            support_levels=supports,
            resistance_levels=resistances,
            market_structure=structure,
            market_regime=regime,
            summary=summary,
            timestamp=datetime.now(timezone.utc)
        )
