import math
from typing import List, Dict, Any, Tuple, Optional, Sequence, Union
from datetime import datetime, timezone
from app.schemas.schemas import (
    TechnicalAnalysisResult, MACDResult, BollingerBandsResult,
    MarketStructureResult, MarketRegimeResult, MultiTimeframeSummary,
    TimeframeAlignment, ConfidenceScoreBreakdown, SignalInvalidation,
    IndicatorEvidence, VolumeMetrics, SupportResistanceBuffer,
    PivotLevels, PivotPointsResult, TechnicalGaugeScore, TechnicalGaugeResult,
    CandlePatternResult, OrderBlockResult, FairValueGapResult,
    LiquiditySweepResult, SmartMoneyConceptsResult
)

class TechnicalAnalysisService:
    @staticmethod
    def calculate_ema(prices: Sequence[Union[float, int]], period: int) -> float:
        if not prices or len(prices) < period:
            return float(prices[-1]) if prices else 0.0
        k = 2.0 / (period + 1.0)
        ema = float(sum(prices[:period])) / period
        for price in prices[period:]:
            ema = (float(price) * k) + (ema * (1.0 - k))
        return round(ema, 4)

    @staticmethod
    def calculate_sma(prices: Sequence[Union[float, int]], period: int) -> float:
        if not prices or len(prices) < period:
            return float(prices[-1]) if prices else 0.0
        return round(float(sum(prices[-period:])) / period, 4)

    @staticmethod
    def calculate_rsi(prices: Sequence[Union[float, int]], period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50.0
        gains, losses = [], []
        for i in range(1, len(prices)):
            diff = float(prices[i]) - float(prices[i - 1])
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
    def calculate_macd(prices: Sequence[Union[float, int]], fast: int = 12, slow: int = 26, signal_period: int = 9) -> MACDResult:
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
    def calculate_bollinger_bands(prices: Sequence[Union[float, int]], period: int = 20, num_std: float = 2.0) -> BollingerBandsResult:
        if len(prices) < period:
            p = float(prices[-1]) if prices else 0.0
            return BollingerBandsResult(upper=p, middle=p, lower=p)
        
        recent = [float(x) for x in prices[-period:]]
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
    def calculate_volume_metrics(candles: List[Dict[str, Any]], period: int = 20) -> VolumeMetrics:
        """Calculates volume trend, spike multiplier, and confirmation status"""
        if len(candles) < 5:
            return VolumeMetrics(
                trend="STABLE",
                spike_ratio=1.0,
                is_volume_confirmed=True,
                interpretation="Standard baseline volume depth."
            )

        volumes = [c.get("volume", 100.0) for c in candles]
        current_vol = volumes[-1]
        recent_window = volumes[-period:] if len(volumes) >= period else volumes
        avg_vol = sum(recent_window) / len(recent_window) if recent_window else 1.0

        spike_ratio = round(current_vol / max(1.0, avg_vol), 2)
        
        # Determine trend of volume over last 5 candles
        last_5 = volumes[-5:]
        if last_5[-1] > last_5[0] * 1.2:
            trend = "INCREASING"
        elif last_5[-1] < last_5[0] * 0.8:
            trend = "DECREASING"
        else:
            trend = "STABLE"

        is_confirmed = spike_ratio >= 1.15
        if spike_ratio >= 1.5:
            interp = f"Significant Institutional Volume Surge ({spike_ratio}x 20-period avg)."
        elif spike_ratio <= 0.7:
            interp = f"Volume drying up ({spike_ratio}x avg), indicates low conviction."
        else:
            interp = f"Normal liquidity participation ({spike_ratio}x avg)."

        return VolumeMetrics(
            trend=trend,
            spike_ratio=spike_ratio,
            is_volume_confirmed=is_confirmed,
            interpretation=interp
        )

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
    def validate_sr_buffer(
        cls,
        current_price: float,
        trend: str,
        supports: List[float],
        resistances: List[float],
        atr: float
    ) -> SupportResistanceBuffer:
        """
        Validates whether there is sufficient headroom between ENTRY and overhead RESISTANCE (for BUY)
        or underlying SUPPORT (for SELL). Rejects buying directly under ceiling resistance!
        """
        min_buffer = atr * 1.5
        overhead_resistances = [r for r in resistances if r > current_price]
        underlying_supports = [s for s in supports if s < current_price]

        nearest_res = min(overhead_resistances) if overhead_resistances else None
        nearest_sup = max(underlying_supports) if underlying_supports else None

        dist_res = round(nearest_res - current_price, 4) if nearest_res else None
        dist_sup = round(current_price - nearest_sup, 4) if nearest_sup else None

        has_headroom = True
        verdict = "Sufficient clearance to nearest structural levels."

        if trend == "bullish" and dist_res is not None:
            if dist_res < min_buffer:
                has_headroom = False
                verdict = f"Insufficient headroom: Price is only {dist_res:.2f} pts from overhead resistance (${nearest_res:.2f}). Wait for confirmed breakout."
        elif trend == "bearish" and dist_sup is not None:
            if dist_sup < min_buffer:
                has_headroom = False
                verdict = f"Insufficient headroom: Price is only {dist_sup:.2f} pts from support floor (${nearest_sup:.2f}). Wait for breakdown."

        return SupportResistanceBuffer(
            has_sufficient_headroom=has_headroom,
            nearest_support=nearest_sup,
            nearest_resistance=nearest_res,
            distance_to_resistance=dist_res,
            distance_to_support=dist_sup,
            verdict=verdict
        )

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
                pattern = "HH → HL → HH (Bullish Trend Structure)"
                structure_bias = "BULLISH"
                if current_close > swing_highs[-1]:
                    bos = True
                    recent_bos = swing_highs[-1]
            elif lh and ll:
                pattern = "LH → LL → LH (Bearish Trend Structure)"
                structure_bias = "BEARISH"
                if current_close < swing_lows[-1]:
                    bos = True
                    recent_bos = swing_lows[-1]
            elif hh and not hl:
                pattern = "CHoCH (Bullish Reversal Shift)"
                structure_bias = "BULLISH"
                choch = True
                recent_choch = swing_highs[-2]
            elif ll and not lh:
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
        Classifies Market Regime with Phase 4 Volatility Squeeze Detection:
        - STRONG_TREND: High ADX (>25), clear EMA stacking, structure alignment
        - WEAK_TREND: Mild slope, ADX 18-25
        - RANGE: ADX < 18, price oscillating near BB middle
        - BREAKOUT / SQUEEZE_EXPANSION: Price piercing BB bands with Keltner expansion
        - SQUEEZE_COMPRESSION: Bollinger Bands contracted inside Keltner Channels (Energy coiling)
        - PULLBACK: Trend intact but short-term counter-move to EMA 20/50 support
        - HIGH_VOLATILITY: ATR expansion or extreme BB width
        """
        bb_width = ((bb.upper - bb.lower) / bb.middle) if bb.middle > 0 else 0.0
        keltner_upper = ema_20 + (1.5 * atr)
        keltner_lower = ema_20 - (1.5 * atr)
        is_squeeze = (bb.lower > keltner_lower) and (bb.upper < keltner_upper)

        if is_squeeze:
            regime = "RANGE"
            confidence = 85.0
            volatility_state = "COMPRESSING"
            rec = "TTM Volatility Squeeze active: Price coiling tightly inside Keltner channel. Prepare for high-velocity breakout."
        elif current_close > bb.upper or current_close < bb.lower:
            regime = "BREAKOUT"
            confidence = 89.0
            volatility_state = "EXPANDING"
            rec = "Volatility Expansion underway: Bands piercing outer channel. Ride momentum with trailing stops."
        elif adx >= 28 and ((current_close > ema_20 > ema_50) or (current_close < ema_20 < ema_50)):
            regime = "STRONG_TREND"
            confidence = 92.0
            volatility_state = "NORMAL"
            rec = "Trade trend continuation pullbacks with directional momentum."
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
        elif adx < 20 or structure.structure_bias == "RANGING":
            regime = "RANGE"
            confidence = 80.0
            volatility_state = "COMPRESSING"
            rec = "Fade range extremes at verified Support & Resistance boundaries."
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

    _cache: Dict[str, Tuple[float, Any]] = {}
    _CACHE_TTL_SECONDS: float = 15.0

    @classmethod
    def analyze(cls, symbol: str, timeframe: str, candles: List[Dict[str, Any]]) -> TechnicalAnalysisResult:
        now = datetime.now(timezone.utc)
        if not candles:
            return TechnicalAnalysisResult(
                symbol=symbol,
                timeframe=timeframe,
                trend="neutral",
                momentum="moderate",
                rsi=50.0,
                macd=MACDResult(value=0, signal=0, histogram=0),
                ema_20=0, ema_50=0, ema_100=0, ema_200=0,
                sma_20=0, sma_50=0, sma_200=0,
                atr=1.0,
                adx=25.0,
                stochastic_k=50.0,
                stochastic_d=50.0,
                bollinger_bands=BollingerBandsResult(upper=0, middle=0, lower=0),
                volume_metrics=None,
                support_levels=[],
                resistance_levels=[],
                sr_buffer=None,
                indicator_evidence={},
                market_structure=None,
                market_regime=None,
                summary="Insufficient candle data for quantitative scan.",
                timestamp=now
            )

        # Check in-memory calculation cache
        latest_c = candles[-1]
        cache_key = f"{symbol.upper()}_{timeframe.lower()}_{latest_c.get('time', '')}_{latest_c.get('close', '')}_{len(candles)}"
        now_ts = now.timestamp()

        if cache_key in cls._cache:
            cached_time, cached_result = cls._cache[cache_key]
            if (now_ts - cached_time) < cls._CACHE_TTL_SECONDS:
                return cached_result

        closes = [c["close"] for c in candles]
        current_close = closes[-1]

        rsi = cls.calculate_rsi(closes, period=14)
        macd = cls.calculate_macd(closes)
        ema_20 = cls.calculate_ema(closes, 20)
        ema_50 = cls.calculate_ema(closes, 50)
        ema_100 = cls.calculate_ema(closes, 100 if len(closes) >= 100 else len(closes))
        ema_200 = cls.calculate_ema(closes, 200 if len(closes) >= 200 else len(closes))
        sma_20 = cls.calculate_sma(closes, 20)
        sma_50 = cls.calculate_sma(closes, 50)
        sma_200 = cls.calculate_sma(closes, 200 if len(closes) >= 200 else len(closes))
        atr = cls.calculate_atr(candles, 14)
        adx = cls.calculate_adx(candles, 14)
        stoch_k, stoch_d = cls.calculate_stochastic(candles, 14, 3)
        bb = cls.calculate_bollinger_bands(closes, 20)
        volume_m = cls.calculate_volume_metrics(candles)
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

        # Check Support & Resistance Headroom
        sr_buf = cls.validate_sr_buffer(current_close, trend, supports, resistances, atr)

        # Build Standardized Indicator Evidence Dictionary
        evidence = {
            "rsi": IndicatorEvidence(
                value=rsi,
                direction="bullish" if rsi > 55 else "bearish" if rsi < 45 else "neutral",
                interpretation=f"RSI is at {rsi:.1f} ({'Strong Bullish' if rsi > 60 else 'Bearish Pressure' if rsi < 40 else 'Neutral Median'}).",
                strength=round(abs(rsi - 50.0) / 50.0, 2),
                timestamp=now
            ),
            "macd": IndicatorEvidence(
                value=macd.histogram,
                direction="bullish" if macd.histogram > 0 else "bearish",
                interpretation=f"MACD histogram is {macd.histogram:+.4f} with {'positive' if macd.value > macd.signal else 'negative'} signal line crossover.",
                strength=0.85 if abs(macd.histogram) > atr * 0.1 else 0.5,
                timestamp=now
            ),
            "adx": IndicatorEvidence(
                value=adx,
                direction="bullish" if adx > 25 and trend == "bullish" else "bearish" if adx > 25 and trend == "bearish" else "neutral",
                interpretation=f"ADX at {adx:.1f} indicates {'Strong Trending Edge' if adx > 25 else 'Chop / Range Bound Market'}.",
                strength=round(min(1.0, adx / 40.0), 2),
                timestamp=now
            ),
            "stochastic": IndicatorEvidence(
                value=stoch_k,
                direction="bullish" if stoch_k > stoch_d and stoch_k < 80 else "bearish" if stoch_k < stoch_d and stoch_k > 20 else "neutral",
                interpretation=f"Stoch %K ({stoch_k:.1f}) and %D ({stoch_d:.1f}) {'bullish expansion' if stoch_k > stoch_d else 'bearish cycle'}.",
                strength=0.75,
                timestamp=now
            ),
            "ema_trend": IndicatorEvidence(
                value=ema_20,
                direction="bullish" if ema_20 > ema_50 else "bearish",
                interpretation=f"EMA 20 (${ema_20:.2f}) {'leads' if ema_20 > ema_50 else 'trails'} EMA 50 (${ema_50:.2f}) and EMA 200 (${ema_200:.2f}).",
                strength=0.90,
                timestamp=now
            )
        }

        summary = (
            f"{trend.upper()} bias on {timeframe} ({structure.pattern}). "
            f"RSI: {rsi}, ADX: {adx} ({regime.regime.replace('_', ' ')}). "
            f"EMA 20/50/200 alignment: {'Bullish' if ema_20 > ema_50 else 'Bearish'}. "
            f"SR Headroom: {sr_buf.verdict}"
        )

        res = TechnicalAnalysisResult(
            symbol=symbol,
            timeframe=timeframe,
            trend=trend,
            momentum=momentum,
            rsi=rsi,
            macd=macd,
            ema_20=ema_20,
            ema_50=ema_50,
            ema_100=ema_100,
            ema_200=ema_200,
            sma_20=sma_20,
            sma_50=sma_50,
            sma_200=sma_200,
            atr=atr,
            adx=adx,
            stochastic_k=stoch_k,
            stochastic_d=stoch_d,
            bollinger_bands=bb,
            volume_metrics=volume_m,
            support_levels=supports,
            resistance_levels=resistances,
            sr_buffer=sr_buf,
            indicator_evidence=evidence,
            market_structure=structure,
            market_regime=regime,
            summary=summary,
            timestamp=now
        )

        cls._cache[cache_key] = (now_ts, res)
        # Limit cache size to 200 entries
        if len(cls._cache) > 200:
            cls._cache.pop(next(iter(cls._cache)))

        return res

    @staticmethod
    def calculate_pivot_points(candles: List[Dict[str, Any]]) -> PivotPointsResult:
        """Calculates Classic, Fibonacci, and Camarilla Pivot Points based on recent candle range"""
        if not candles:
            dummy = PivotLevels(pivot=0, r1=0, r2=0, r3=0, s1=0, s2=0, s3=0)
            return PivotPointsResult(classic=dummy, fibonacci=dummy, camarilla=dummy)

        # Look at last completed session / range (up to last 24 candles or 1-day range)
        subset = candles[-24:] if len(candles) >= 24 else candles
        high = max(c["high"] for c in subset)
        low = min(c["low"] for c in subset)
        close = subset[-1]["close"]
        diff = high - low

        # Classic
        p_classic = (high + low + close) / 3.0
        classic = PivotLevels(
            pivot=round(p_classic, 2),
            r1=round(2 * p_classic - low, 2),
            r2=round(p_classic + diff, 2),
            r3=round(high + 2 * (p_classic - low), 2),
            s1=round(2 * p_classic - high, 2),
            s2=round(p_classic - diff, 2),
            s3=round(low - 2 * (high - p_classic), 2),
        )

        # Fibonacci
        fib = PivotLevels(
            pivot=round(p_classic, 2),
            r1=round(p_classic + 0.382 * diff, 2),
            r2=round(p_classic + 0.618 * diff, 2),
            r3=round(p_classic + 1.000 * diff, 2),
            s1=round(p_classic - 0.382 * diff, 2),
            s2=round(p_classic - 0.618 * diff, 2),
            s3=round(p_classic - 1.000 * diff, 2),
        )

        # Camarilla
        cam = PivotLevels(
            pivot=round(p_classic, 2),
            r1=round(close + diff * 1.1 / 12.0, 2),
            r2=round(close + diff * 1.1 / 6.0, 2),
            r3=round(close + diff * 1.1 / 4.0, 2),
            s1=round(close - diff * 1.1 / 12.0, 2),
            s2=round(close - diff * 1.1 / 6.0, 2),
            s3=round(close - diff * 1.1 / 4.0, 2),
        )

        return PivotPointsResult(classic=classic, fibonacci=fib, camarilla=cam)

    @staticmethod
    def detect_candlestick_patterns(candles: List[Dict[str, Any]]) -> List[CandlePatternResult]:
        """Detects high-probability institutional candlestick patterns on the latest candles"""
        patterns = []
        if len(candles) < 3:
            return patterns

        c1 = candles[-3]
        c2 = candles[-2]
        c3 = candles[-1]

        body3 = abs(c3["close"] - c3["open"])
        range3 = c3["high"] - c3["low"]
        upper_wick3 = c3["high"] - max(c3["open"], c3["close"])
        lower_wick3 = min(c3["open"], c3["close"]) - c3["low"]

        # 1. Bullish Engulfing
        if c2["close"] < c2["open"] and c3["close"] > c3["open"] and c3["close"] >= c2["open"] and c3["open"] <= c2["close"]:
            patterns.append(CandlePatternResult(
                pattern_name="Bullish Engulfing",
                pattern_type="BULLISH",
                significance="HIGH",
                description="Strong buying absorption engulfing prior selling candle. High probability reversal."
            ))

        # 2. Bearish Engulfing
        if c2["close"] > c2["open"] and c3["close"] < c3["open"] and c3["close"] <= c2["open"] and c3["open"] >= c2["close"]:
            patterns.append(CandlePatternResult(
                pattern_name="Bearish Engulfing",
                pattern_type="BEARISH",
                significance="HIGH",
                description="Aggressive selling pressure engulfing prior bullish candle."
            ))

        # 3. Hammer / Bullish Pinbar
        if range3 > 0 and (lower_wick3 >= 2.0 * body3) and (upper_wick3 <= 0.25 * range3):
            patterns.append(CandlePatternResult(
                pattern_name="Hammer (Demand Rejection)",
                pattern_type="BULLISH",
                significance="MEDIUM",
                description="Significant lower shadow showing aggressive buyer defense at lows."
            ))

        # 4. Shooting Star / Bearish Pinbar
        if range3 > 0 and (upper_wick3 >= 2.0 * body3) and (lower_wick3 <= 0.25 * range3):
            patterns.append(CandlePatternResult(
                pattern_name="Shooting Star (Supply Rejection)",
                pattern_type="BEARISH",
                significance="MEDIUM",
                description="Strong rejection from highs. Sellers defended upper resistance."
            ))

        # 5. Morning Star
        if (c1["close"] < c1["open"] and
            abs(c2["close"] - c2["open"]) < 0.3 * (c1["high"] - c1["low"]) and
            c3["close"] > c3["open"] and
            c3["close"] > (c1["open"] + c1["close"]) / 2):
            patterns.append(CandlePatternResult(
                pattern_name="Morning Star",
                pattern_type="BULLISH",
                significance="HIGH",
                description="3-Bar reversal cluster confirming transition from exhaustion to expansion."
            ))

        # 6. Evening Star
        if (c1["close"] > c1["open"] and
            abs(c2["close"] - c2["open"]) < 0.3 * (c1["high"] - c1["low"]) and
            c3["close"] < c3["open"] and
            c3["close"] < (c1["open"] + c1["close"]) / 2):
            patterns.append(CandlePatternResult(
                pattern_name="Evening Star",
                pattern_type="BEARISH",
                significance="HIGH",
                description="3-Bar top reversal cluster indicating heavy distribution."
            ))

        # 7. Doji (Indecision)
        if range3 > 0 and (body3 / range3) < 0.10:
            patterns.append(CandlePatternResult(
                pattern_name="Doji (Market Indecision)",
                pattern_type="NEUTRAL",
                significance="LOW",
                description="Equilibrium between buyers and sellers awaiting directional catalyst."
            ))

        if not patterns:
            patterns.append(CandlePatternResult(
                pattern_name="Trend Continuity Bar",
                pattern_type="BULLISH" if c3["close"] >= c3["open"] else "BEARISH",
                significance="LOW",
                description="Price action expanding within prevailing structural order flow."
            ))

        return patterns

    @staticmethod
    def detect_order_blocks(candles: List[Dict[str, Any]], timeframe: str = "1h") -> List[OrderBlockResult]:
        """Detects institutional Order Blocks (OBs) - last down/up candles before strong directional expansion"""
        order_blocks = []
        if len(candles) < 10:
            return order_blocks

        for i in range(len(candles) - 6, len(candles) - 2):
            c_curr = candles[i]
            c_next = candles[i + 1]
            c_after = candles[i + 2]

            # Bullish Order Block (last bearish candle before sharp upward rally)
            if (c_curr["close"] < c_curr["open"] and
                c_next["close"] > c_next["open"] and
                c_after["close"] > c_curr["high"] and
                (c_next["close"] - c_next["open"]) > (c_curr["open"] - c_curr["close"]) * 1.5):
                # Check if mitigated
                is_mit = any(candles[j]["low"] < c_curr["low"] for j in range(i + 3, len(candles)))
                order_blocks.append(OrderBlockResult(
                    block_type="BULLISH_DEMAND",
                    price_high=c_curr["high"],
                    price_low=c_curr["low"],
                    timeframe=timeframe,
                    is_mitigated=is_mit
                ))

            # Bearish Order Block (last bullish candle before sharp downward plunge)
            if (c_curr["close"] > c_curr["open"] and
                c_next["close"] < c_next["open"] and
                c_after["close"] < c_curr["low"] and
                (c_next["open"] - c_next["close"]) > (c_curr["close"] - c_curr["open"]) * 1.5):
                is_mit = any(candles[j]["high"] > c_curr["high"] for j in range(i + 3, len(candles)))
                order_blocks.append(OrderBlockResult(
                    block_type="BEARISH_SUPPLY",
                    price_high=c_curr["high"],
                    price_low=c_curr["low"],
                    timeframe=timeframe,
                    is_mitigated=is_mit
                ))

        return order_blocks[-4:]

    @staticmethod
    def detect_fair_value_gaps(candles: List[Dict[str, Any]], timeframe: str = "1h") -> List[FairValueGapResult]:
        """
        Detects institutional 3-candle Fair Value Gaps (FVG / Imbalances):
        - Bullish FVG: Candle 3 Low > Candle 1 High (Unfilled upward liquidity void)
        - Bearish FVG: Candle 3 High < Candle 1 Low (Unfilled downward liquidity void)
        - Midpoint (CE - Consequent Encroachment): 50% retest target
        """
        fvgs = []
        if len(candles) < 4:
            return fvgs

        for i in range(1, len(candles) - 1):
            c1 = candles[i - 1]
            c2 = candles[i]
            c3 = candles[i + 1]

            # Bullish FVG
            if c2["close"] > c2["open"] and c3["low"] > c1["high"]:
                gap_top = round(float(c3["low"]), 4)
                gap_bottom = round(float(c1["high"]), 4)
                ce = round((gap_top + gap_bottom) / 2.0, 4)
                # Check if mitigated by any subsequent candle
                is_mitigated = any(candles[j]["low"] <= gap_bottom for j in range(i + 2, len(candles)))
                fvgs.append(FairValueGapResult(
                    fvg_type="BULLISH_FVG",
                    top=gap_top,
                    bottom=gap_bottom,
                    midpoint=ce,
                    timeframe=timeframe,
                    is_mitigated=is_mitigated,
                    description=f"Bullish Imbalance [${gap_bottom:.2f} - ${gap_top:.2f}] with 50% CE @ ${ce:.2f}"
                ))

            # Bearish FVG
            elif c2["close"] < c2["open"] and c3["high"] < c1["low"]:
                gap_top = round(float(c1["low"]), 4)
                gap_bottom = round(float(c3["high"]), 4)
                ce = round((gap_top + gap_bottom) / 2.0, 4)
                # Check if mitigated by any subsequent candle
                is_mitigated = any(candles[j]["high"] >= gap_top for j in range(i + 2, len(candles)))
                fvgs.append(FairValueGapResult(
                    fvg_type="BEARISH_FVG",
                    top=gap_top,
                    bottom=gap_bottom,
                    midpoint=ce,
                    timeframe=timeframe,
                    is_mitigated=is_mitigated,
                    description=f"Bearish Imbalance [${gap_bottom:.2f} - ${gap_top:.2f}] with 50% CE @ ${ce:.2f}"
                ))

        return fvgs[-5:]

    @staticmethod
    def detect_liquidity_sweeps(candles: List[Dict[str, Any]], timeframe: str = "1h") -> List[LiquiditySweepResult]:
        """
        Detects institutional Liquidity Sweeps / Stop Runs:
        - Buy-Side Liquidity (BSL) Sweep: Wick spikes above swing high but closes back below (Bull Trap)
        - Sell-Side Liquidity (SSL) Sweep: Wick spikes below swing low but closes back above (Bear Trap)
        """
        sweeps = []
        if len(candles) < 15:
            return sweeps

        # Identify recent swing highs and swing lows (lookback 10 candles)
        for i in range(10, len(candles) - 1):
            prior_highs = [candles[j]["high"] for j in range(max(0, i - 8), i)]
            prior_lows = [candles[j]["low"] for j in range(max(0, i - 8), i)]
            
            if not prior_highs or not prior_lows:
                continue

            swing_high = max(prior_highs)
            swing_low = min(prior_lows)

            c = candles[i]
            # BSL Sweep (High pierced swing high, but close failed below it with long upper wick)
            upper_wick = c["high"] - max(c["open"], c["close"])
            body = abs(c["close"] - c["open"])
            if c["high"] > swing_high and c["close"] < swing_high and upper_wick > body:
                sweeps.append(LiquiditySweepResult(
                    sweep_type="BUY_SIDE_LIQUIDITY_SWEEP",
                    swept_level=round(float(swing_high), 4),
                    reversal_bias="BEARISH",
                    timeframe=timeframe,
                    description=f"Buy-Side Liquidity swept @ ${swing_high:.2f} (Bearish Reversal Wick)"
                ))

            # SSL Sweep (Low pierced swing low, but close held above it with long lower wick)
            lower_wick = min(c["open"], c["close"]) - c["low"]
            if c["low"] < swing_low and c["close"] > swing_low and lower_wick > body:
                sweeps.append(LiquiditySweepResult(
                    sweep_type="SELL_SIDE_LIQUIDITY_SWEEP",
                    swept_level=round(float(swing_low), 4),
                    reversal_bias="BULLISH",
                    timeframe=timeframe,
                    description=f"Sell-Side Liquidity swept @ ${swing_low:.2f} (Bullish Reversal Wick)"
                ))

        return sweeps[-4:]

    @classmethod
    def calculate_smart_money_concepts(
        cls,
        candles: List[Dict[str, Any]],
        timeframe: str = "1h",
        current_price: float = 0.0
    ) -> SmartMoneyConceptsResult:
        """
        Synthesizes complete institutional Smart Money Concepts (SMC):
        - Order Blocks (Demand / Supply)
        - Fair Value Gaps (FVG)
        - Liquidity Sweeps
        - Premium vs Discount Equilibrium Range Analysis
        - SMC Bias & Confluence Score
        """
        obs = cls.detect_order_blocks(candles, timeframe=timeframe)
        fvgs = cls.detect_fair_value_gaps(candles, timeframe=timeframe)
        sweeps = cls.detect_liquidity_sweeps(candles, timeframe=timeframe)

        if not candles:
            return SmartMoneyConceptsResult(
                order_blocks=[],
                fair_value_gaps=[],
                liquidity_sweeps=[],
                premium_discount_zone="EQUILIBRIUM",
                equilibrium_price=current_price,
                smc_bias="NEUTRAL",
                smc_confluence_score=50.0,
                institutional_verdict="Insufficient candle data for SMC analysis."
            )

        if current_price <= 0.0:
            current_price = float(candles[-1]["close"])

        # Determine Range Equilibrium (lookback 30 candles)
        lookback = candles[-30:] if len(candles) >= 30 else candles
        range_high = max(c["high"] for c in lookback)
        range_low = min(c["low"] for c in lookback)
        equilibrium = round((range_high + range_low) / 2.0, 4)
        range_size = range_high - range_low

        if range_size > 0:
            pct_from_low = (current_price - range_low) / range_size
            if pct_from_low > 0.55:
                zone = "PREMIUM_OVERVALUED"
            elif pct_from_low < 0.45:
                zone = "DISCOUNT_UNDERVALUED"
            else:
                zone = "EQUILIBRIUM"
        else:
            zone = "EQUILIBRIUM"

        # Confluence calculation
        bull_pts = 0.0
        bear_pts = 0.0

        # 1. Premium / Discount Zone
        if zone == "DISCOUNT_UNDERVALUED":
            bull_pts += 30.0
        elif zone == "PREMIUM_OVERVALUED":
            bear_pts += 30.0
        else:
            bull_pts += 15.0
            bear_pts += 15.0

        # 2. Unmitigated FVGs
        unmit_bull_fvg = [f for f in fvgs if f.fvg_type == "BULLISH_FVG" and not f.is_mitigated]
        unmit_bear_fvg = [f for f in fvgs if f.fvg_type == "BEARISH_FVG" and not f.is_mitigated]
        if unmit_bull_fvg:
            bull_pts += min(30.0, len(unmit_bull_fvg) * 15.0)
        if unmit_bear_fvg:
            bear_pts += min(30.0, len(unmit_bear_fvg) * 15.0)

        # 3. Order Blocks
        demand_obs = [ob for ob in obs if ob.block_type == "BULLISH_DEMAND" and not ob.is_mitigated]
        supply_obs = [ob for ob in obs if ob.block_type == "BEARISH_SUPPLY" and not ob.is_mitigated]
        if demand_obs:
            bull_pts += min(25.0, len(demand_obs) * 15.0)
        if supply_obs:
            bear_pts += min(25.0, len(supply_obs) * 15.0)

        # 4. Liquidity Sweeps
        recent_sweeps = sweeps[-2:] if sweeps else []
        for sw in recent_sweeps:
            if sw.reversal_bias == "BULLISH":
                bull_pts += 20.0
            elif sw.reversal_bias == "BEARISH":
                bear_pts += 20.0

        total_pts = bull_pts + bear_pts
        if total_pts == 0:
            smc_bias = "NEUTRAL"
            score = 50.0
            verdict = "Neutral institutional positioning. Price hovering around equilibrium."
        elif bull_pts >= bear_pts + 30.0:
            smc_bias = "STRONG_BULLISH"
            score = min(96.0, 70.0 + (bull_pts - bear_pts) * 0.4)
            verdict = f"High-Conviction Institutional Accumulation: Price in Discount (${current_price:.2f} < Eq ${equilibrium:.2f}) with active Demand Order Blocks."
        elif bull_pts > bear_pts + 10.0:
            smc_bias = "BULLISH"
            score = min(88.0, 60.0 + (bull_pts - bear_pts) * 0.4)
            verdict = "Bullish Smart Money order flow supported by discount liquidity."
        elif bear_pts >= bull_pts + 30.0:
            smc_bias = "STRONG_BEARISH"
            score = min(96.0, 70.0 + (bear_pts - bull_pts) * 0.4)
            verdict = f"High-Conviction Institutional Distribution: Price in Premium (${current_price:.2f} > Eq ${equilibrium:.2f}) under active Supply Order Blocks."
        elif bear_pts > bull_pts + 10.0:
            smc_bias = "BEARISH"
            score = min(88.0, 60.0 + (bear_pts - bull_pts) * 0.4)
            verdict = "Bearish Smart Money distribution pressure from overhead supply."
        else:
            smc_bias = "NEUTRAL"
            score = 50.0
            verdict = "Equilibrium order flow. Awaiting liquidity sweep or imbalance expansion."

        return SmartMoneyConceptsResult(
            order_blocks=obs,
            fair_value_gaps=fvgs,
            liquidity_sweeps=sweeps,
            premium_discount_zone=zone,
            equilibrium_price=equilibrium,
            smc_bias=smc_bias,
            smc_confluence_score=round(score, 1),
            institutional_verdict=verdict
        )

    @classmethod
    def calculate_technical_gauge(cls, tech: TechnicalAnalysisResult, closes: List[float], current_price: float) -> TechnicalGaugeResult:
        """
        Computes institutional TradingView-style Gauge:
        - Oscillators: RSI, MACD, Stochastic, ADX, CCI, Bollinger %B
        - Moving Averages: EMA 10, 20, 50, 100, 200, SMA 20, 50, 200
        - Overall summary: STRONG_BUY, BUY, NEUTRAL, SELL, STRONG_SELL
        """
        # 1. Moving Averages evaluation
        ma_buy = 0
        ma_sell = 0
        ma_neutral = 0

        mas = [
            tech.ema_20, tech.ema_50, tech.ema_100 or tech.ema_50, tech.ema_200,
            tech.sma_20 or tech.ema_20, tech.sma_50 or tech.ema_50, tech.sma_200 or tech.ema_200
        ]
        for ma in mas:
            if ma > 0:
                if current_price > ma * 1.001:
                    ma_buy += 1
                elif current_price < ma * 0.999:
                    ma_sell += 1
                else:
                    ma_neutral += 1

        ma_total = ma_buy + ma_sell + ma_neutral
        ma_summary = "NEUTRAL"
        if ma_buy >= ma_total * 0.7:
            ma_summary = "STRONG_BUY"
        elif ma_buy >= ma_total * 0.5:
            ma_summary = "BUY"
        elif ma_sell >= ma_total * 0.7:
            ma_summary = "STRONG_SELL"
        elif ma_sell >= ma_total * 0.5:
            ma_summary = "SELL"

        ma_score = TechnicalGaugeScore(
            buy_count=ma_buy,
            sell_count=ma_sell,
            neutral_count=ma_neutral,
            summary=ma_summary
        )

        # 2. Oscillators evaluation
        osc_buy = 0
        osc_sell = 0
        osc_neutral = 0

        # RSI 14
        if tech.rsi > 55 and tech.rsi < 70:
            osc_buy += 1
        elif tech.rsi < 45 and tech.rsi > 30:
            osc_sell += 1
        elif tech.rsi <= 30: # Oversold reversal opportunity
            osc_buy += 1
        elif tech.rsi >= 70: # Overbought risk
            osc_sell += 1
        else:
            osc_neutral += 1

        # MACD
        if tech.macd.histogram > 0:
            osc_buy += 1
        elif tech.macd.histogram < 0:
            osc_sell += 1
        else:
            osc_neutral += 1

        # Stochastic
        if tech.stochastic_k and tech.stochastic_d:
            if tech.stochastic_k > tech.stochastic_d and tech.stochastic_k < 80:
                osc_buy += 1
            elif tech.stochastic_k < tech.stochastic_d and tech.stochastic_k > 20:
                osc_sell += 1
            else:
                osc_neutral += 1

        # ADX
        if tech.adx and tech.adx > 25:
            if tech.trend == "bullish":
                osc_buy += 1
            elif tech.trend == "bearish":
                osc_sell += 1
            else:
                osc_neutral += 1
        else:
            osc_neutral += 1

        # Bollinger %B
        bb_range = tech.bollinger_bands.upper - tech.bollinger_bands.lower
        if bb_range > 0:
            pct_b = (current_price - tech.bollinger_bands.lower) / bb_range
            if pct_b > 0.6:
                osc_buy += 1
            elif pct_b < 0.4:
                osc_sell += 1
            else:
                osc_neutral += 1

        osc_total = osc_buy + osc_sell + osc_neutral
        osc_summary = "NEUTRAL"
        if osc_buy >= osc_total * 0.65:
            osc_summary = "STRONG_BUY"
        elif osc_buy >= osc_total * 0.5:
            osc_summary = "BUY"
        elif osc_sell >= osc_total * 0.65:
            osc_summary = "STRONG_SELL"
        elif osc_sell >= osc_total * 0.5:
            osc_summary = "SELL"

        osc_score = TechnicalGaugeScore(
            buy_count=osc_buy,
            sell_count=osc_sell,
            neutral_count=osc_neutral,
            summary=osc_summary
        )

        # 3. Overall
        total_buy = ma_buy + osc_buy
        total_sell = ma_sell + osc_sell
        total_neutral = ma_neutral + osc_neutral
        grand_total = max(1, total_buy + total_sell + total_neutral)

        overall_pct = (total_buy / grand_total) * 100.0
        overall_summary = "NEUTRAL"
        if overall_pct >= 68:
            overall_summary = "STRONG_BUY"
        elif overall_pct >= 52:
            overall_summary = "BUY"
        elif (total_sell / grand_total) * 100.0 >= 68:
            overall_summary = "STRONG_SELL"
        elif (total_sell / grand_total) * 100.0 >= 52:
            overall_summary = "SELL"

        overall_score = TechnicalGaugeScore(
            buy_count=total_buy,
            sell_count=total_sell,
            neutral_count=total_neutral,
            summary=overall_summary
        )

        return TechnicalGaugeResult(
            oscillators=osc_score,
            moving_averages=ma_score,
            overall=overall_score,
            score_percentage=round(overall_pct, 1)
        )

    @staticmethod
    def get_current_trading_session() -> Dict[str, Any]:
        """
        Phase 3: Computes real-time institutional trading sessions & killzones based on UTC:
        - London Open Killzone (07:00 - 10:00 GMT): High liquidity for EUR, GBP, Gold
        - London / New York Overlap (12:30 - 15:30 GMT): Peak global volume for Gold, Equities, USD
        - New York PM Session (16:00 - 20:00 GMT): US equity close & momentum runs
        - Asian Session (22:00 - 07:00 GMT): Lower volume range consolidation
        - London Lunch / Low Volatility (10:00 - 12:30 GMT)
        """
        now_utc = datetime.now(timezone.utc)
        hour = now_utc.hour + (now_utc.minute / 60.0)

        if 12.5 <= hour <= 15.5:
            return {
                "session_name": "LONDON_NY_OVERLAP_KILLZONE",
                "session_label": "London & New York Overlap (Power Hours)",
                "quality": "PRIME_LIQUIDITY",
                "score_multiplier": 1.15,
                "is_killzone": True,
                "description": "Peak global volume & maximum institutional liquidity across Gold, Equities & USD."
            }
        elif 7.0 <= hour <= 10.0:
            return {
                "session_name": "LONDON_OPEN_KILLZONE",
                "session_label": "London Open Killzone",
                "quality": "PRIME_LIQUIDITY",
                "score_multiplier": 1.10,
                "is_killzone": True,
                "description": "High directional liquidity expansion for European pairs, Gold & Commodities."
            }
        elif 16.0 <= hour <= 20.0:
            return {
                "session_name": "NEW_YORK_PM_SESSION",
                "session_label": "New York PM Session",
                "quality": "MODERATE_VOLUME",
                "score_multiplier": 1.00,
                "is_killzone": False,
                "description": "Trend continuation and institutional positioning into NY cash close."
            }
        elif 10.0 < hour < 12.5:
            return {
                "session_name": "LONDON_LUNCH_MIDDAY",
                "session_label": "London Midday / Pre-NY",
                "quality": "MODERATE_VOLUME",
                "score_multiplier": 0.95,
                "is_killzone": False,
                "description": "Interim liquidity window awaiting New York opening volatility."
            }
        else:
            return {
                "session_name": "ASIAN_PACIFIC_SESSION",
                "session_label": "Asian / Pacific Session",
                "quality": "LOW_LIQUIDITY_CAUTION",
                "score_multiplier": 0.85,
                "is_killzone": False,
                "description": "Consolidation ranges. Beware of low liquidity fakeouts outside Asian pairs."
            }

