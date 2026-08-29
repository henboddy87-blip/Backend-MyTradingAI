from typing import Dict, Any, List, Optional
from collections import defaultdict
from sqlalchemy.orm import Session
from app.models.models import SignalOutcome, Signal
from app.schemas.schemas import (
    TrackRecordSummaryOut, EquityPoint, PerformanceByAsset,
    PerformanceByTimeframe, MonthlyPerformance
)

class TrackRecordService:
    @classmethod
    def calculate_track_record(
        cls,
        db: Session,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        market_regime: Optional[str] = None,
        min_confidence: Optional[float] = None
    ) -> TrackRecordSummaryOut:
        query = db.query(SignalOutcome).join(Signal, SignalOutcome.signal_id == Signal.id)

        if symbol and symbol.upper() != "ALL":
            query = query.filter(SignalOutcome.symbol == symbol.upper())
        if timeframe and timeframe.lower() != "all":
            query = query.filter(Signal.timeframe == timeframe.lower())
        if min_confidence:
            query = query.filter(Signal.confidence >= min_confidence)

        outcomes = query.order_by(SignalOutcome.recorded_at.asc()).all()
        
        if not outcomes:
            return TrackRecordSummaryOut(
                total_trades=0,
                wins=0,
                losses=0,
                win_rate=0.0,
                loss_rate=0.0,
                average_r=0.0,
                average_win_r=0.0,
                average_loss_r=0.0,
                profit_factor=0.0,
                total_r=0.0,
                max_drawdown_pct=0.0,
                expectancy_r=0.0,
                best_symbol="N/A",
                worst_symbol="N/A",
                equity_curve=[],
                performance_by_asset=[],
                performance_by_timeframe=[],
                monthly_performance=[],
                is_demo_data=True
            )

        total_trades = len(outcomes)
        wins = sum(1 for o in outcomes if o.outcome == "WIN")
        losses = sum(1 for o in outcomes if o.outcome == "LOSS")
        win_rate = round((wins / total_trades) * 100.0, 1) if total_trades > 0 else 0.0
        loss_rate = round((losses / total_trades) * 100.0, 1) if total_trades > 0 else 0.0

        total_r = round(sum(o.pnl_r for o in outcomes), 2)
        avg_r = round(total_r / total_trades, 2) if total_trades > 0 else 0.0

        winning_r_list = [o.pnl_r for o in outcomes if o.pnl_r > 0]
        losing_r_list = [abs(o.pnl_r) for o in outcomes if o.pnl_r < 0]

        avg_win_r = round(sum(winning_r_list) / len(winning_r_list), 2) if winning_r_list else 0.0
        avg_loss_r = round(sum(losing_r_list) / len(losing_r_list), 2) if losing_r_list else 0.0

        gross_profit_r = sum(winning_r_list)
        gross_loss_r = sum(losing_r_list)
        profit_factor = round(gross_profit_r / gross_loss_r, 2) if gross_loss_r > 0 else (round(gross_profit_r, 2) if gross_profit_r > 0 else 1.0)

        # Mathematical Expectancy: EV = (Win_Rate * Avg_Win) - (Loss_Rate * Avg_Loss)
        win_prob = win_rate / 100.0
        loss_prob = loss_rate / 100.0
        expectancy_r = round((win_prob * avg_win_r) - (loss_prob * avg_loss_r), 2)

        # Equity Curve and Maximum Drawdown calculation
        equity_curve: List[EquityPoint] = []
        cumulative_r = 0.0
        base_capital = 10000.0
        current_equity = base_capital
        peak_equity = base_capital
        max_drawdown_pct = 0.0

        for o in outcomes:
            cumulative_r += o.pnl_r
            current_equity += current_equity * (o.pnl_r * 0.015)
            if current_equity > peak_equity:
                peak_equity = current_equity
            
            dd_pct = ((peak_equity - current_equity) / peak_equity) * 100.0
            if dd_pct > max_drawdown_pct:
                max_drawdown_pct = dd_pct

            date_str = o.recorded_at.strftime("%Y-%m-%d")
            equity_curve.append(EquityPoint(
                date=date_str,
                equity=round(current_equity, 2),
                pnl_r=round(cumulative_r, 2)
            ))

        # Performance by Asset
        asset_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"trades": 0, "wins": 0, "total_r": 0.0})
        for o in outcomes:
            asset_stats[o.symbol]["trades"] += 1
            if o.outcome == "WIN":
                asset_stats[o.symbol]["wins"] += 1
            asset_stats[o.symbol]["total_r"] += o.pnl_r

        perf_by_asset: List[PerformanceByAsset] = []
        for sym, stats in asset_stats.items():
            wr = round((stats["wins"] / stats["trades"]) * 100.0, 1) if stats["trades"] > 0 else 0.0
            perf_by_asset.append(PerformanceByAsset(
                symbol=sym,
                trades=stats["trades"],
                win_rate=wr,
                total_r=round(stats["total_r"], 2)
            ))

        perf_by_asset.sort(key=lambda x: x.total_r, reverse=True)
        best_symbol = perf_by_asset[0].symbol if perf_by_asset else "N/A"
        worst_symbol = perf_by_asset[-1].symbol if perf_by_asset else "N/A"

        # Performance by Timeframe
        signals_map = {s.id: s.timeframe for s in db.query(Signal.id, Signal.timeframe).all()}
        tf_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"trades": 0, "wins": 0, "total_r": 0.0})
        for o in outcomes:
            tf = signals_map.get(o.signal_id, "1h")
            tf_stats[tf]["trades"] += 1
            if o.outcome == "WIN":
                tf_stats[tf]["wins"] += 1
            tf_stats[tf]["total_r"] += o.pnl_r

        perf_by_tf: List[PerformanceByTimeframe] = []
        for tf, stats in tf_stats.items():
            wr = round((stats["wins"] / stats["trades"]) * 100.0, 1) if stats["trades"] > 0 else 0.0
            perf_by_tf.append(PerformanceByTimeframe(
                timeframe=tf,
                trades=stats["trades"],
                win_rate=wr,
                total_r=round(stats["total_r"], 2)
            ))

        # Monthly performance
        monthly_map: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"trades": 0, "wins": 0, "pnl_r": 0.0})
        for o in outcomes:
            month_key = o.recorded_at.strftime("%Y-%m")
            monthly_map[month_key]["trades"] += 1
            if o.outcome == "WIN":
                monthly_map[month_key]["wins"] += 1
            monthly_map[month_key]["pnl_r"] += o.pnl_r

        monthly_perf: List[MonthlyPerformance] = []
        for m, stats in sorted(monthly_map.items()):
            wr = round((stats["wins"] / stats["trades"]) * 100.0, 1) if stats["trades"] > 0 else 0.0
            monthly_perf.append(MonthlyPerformance(
                month=m,
                pnl_pct=round(stats["pnl_r"] * 1.5, 1),
                trades=stats["trades"],
                win_rate=wr
            ))

        return TrackRecordSummaryOut(
            total_trades=total_trades,
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            loss_rate=loss_rate,
            average_r=avg_r,
            average_win_r=avg_win_r,
            average_loss_r=avg_loss_r,
            profit_factor=profit_factor,
            total_r=total_r,
            max_drawdown_pct=round(max_drawdown_pct, 1),
            expectancy_r=expectancy_r,
            best_symbol=best_symbol,
            worst_symbol=worst_symbol,
            equity_curve=equity_curve,
            performance_by_asset=perf_by_asset,
            performance_by_timeframe=perf_by_tf,
            monthly_performance=monthly_perf,
            is_demo_data=True
        )
