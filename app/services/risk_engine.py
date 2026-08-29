from typing import Dict, Any, List, Optional, Tuple
from app.schemas.schemas import RiskCalculationRequest, RiskCalculationResponse

class RiskEngine:
    MIN_RR_RATIO: float = 1.2
    MAX_RISK_PCT: float = 5.0
    DEFAULT_MAX_DAILY_LOSS_PCT: float = 4.0

    @classmethod
    def calculate_position_risk(
        cls,
        account_balance: float,
        risk_percentage: float,
        entry: float,
        stop_loss: float,
        take_profit: float,
        direction: str = "BUY"
    ) -> RiskCalculationResponse:
        warnings = []
        is_valid = True

        # Direction checks
        if direction.upper() == "BUY":
            if stop_loss >= entry:
                warnings.append("Invalid Stop Loss: For a BUY trade, Stop Loss must be strictly below Entry price.")
                is_valid = False
            if take_profit <= entry:
                warnings.append("Invalid Take Profit: For a BUY trade, Take Profit must be strictly above Entry price.")
                is_valid = False
            risk_dist = abs(entry - stop_loss)
            reward_dist = abs(take_profit - entry)
        else: # SELL
            if stop_loss <= entry:
                warnings.append("Invalid Stop Loss: For a SELL trade, Stop Loss must be strictly above Entry price.")
                is_valid = False
            if take_profit >= entry:
                warnings.append("Invalid Take Profit: For a SELL trade, Take Profit must be strictly below Entry price.")
                is_valid = False
            risk_dist = abs(stop_loss - entry)
            reward_dist = abs(entry - take_profit)

        if risk_dist <= 0:
            return RiskCalculationResponse(
                account_balance=account_balance,
                risk_amount=0,
                reward_amount=0,
                risk_reward_ratio=0,
                position_size=0,
                price_risk_distance=0,
                price_reward_distance=0,
                is_valid_risk=False,
                warnings=["Invalid zero price risk distance."]
            )

        # Risk amount based on % of account
        risk_amount = round(account_balance * (risk_percentage / 100.0), 2)
        
        # Risk/Reward Ratio
        rr_ratio = round(reward_dist / risk_dist, 2)
        reward_amount = round(risk_amount * rr_ratio, 2)

        # Position size in units
        position_size = round(risk_amount / risk_dist, 4)

        if rr_ratio < cls.MIN_RR_RATIO:
            warnings.append(f"Suboptimal Risk/Reward ratio ({rr_ratio} < {cls.MIN_RR_RATIO}). Setup offers poor asymmetric reward.")
            is_valid = False

        if risk_percentage > cls.MAX_RISK_PCT:
            warnings.append(f"Excessive risk percentage ({risk_percentage}% > {cls.MAX_RISK_PCT}% max allowed).")
            is_valid = False

        return RiskCalculationResponse(
            account_balance=round(account_balance, 2),
            risk_amount=risk_amount,
            reward_amount=reward_amount,
            risk_reward_ratio=rr_ratio,
            position_size=position_size,
            price_risk_distance=round(risk_dist, 4),
            price_reward_distance=round(reward_dist, 4),
            is_valid_risk=is_valid,
            warnings=warnings
        )

    @classmethod
    def validate_trade_setup(
        cls,
        direction: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
        current_daily_loss_pct: float = 0.0
    ) -> Tuple[bool, str]:
        warnings = []
        if current_daily_loss_pct >= cls.DEFAULT_MAX_DAILY_LOSS_PCT:
            return False, f"Maximum daily drawdown limit reached ({current_daily_loss_pct:.1f}%). Trading halted for risk safety."

        calc = cls.calculate_position_risk(10000.0, 1.0, entry, stop_loss, take_profit, direction)
        return calc.is_valid_risk, "; ".join(calc.warnings) if calc.warnings else "Risk parameters verified."

