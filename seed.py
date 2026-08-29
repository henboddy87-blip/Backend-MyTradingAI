import datetime
import random
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models.models import (
    User, Plan, Subscription, Asset, Signal, SignalOutcome,
    TradeJournal, News, NewsSentiment, Watchlist, BlogPost, SystemLog
)

def run_seed():
    print("Seeding database with realistic institutional demo data...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. Clean existing records for fresh idempotent seed
    db.query(SignalOutcome).delete()
    db.query(Signal).delete()
    db.query(TradeJournal).delete()
    db.query(Watchlist).delete()
    db.query(NewsSentiment).delete()
    db.query(News).delete()
    db.query(Subscription).delete()
    db.query(User).delete()
    db.query(Plan).delete()
    db.query(Asset).delete()
    db.query(BlogPost).delete()
    db.commit()

    # 2. Seed Plans
    plans = [
        Plan(
            name="Free Starter",
            code="FREE",
            description="Essential market intelligence & basic trading signals",
            price_monthly=0.0,
            price_yearly=0.0,
            max_signals_per_day=3,
            max_ai_analyses_per_day=5,
            telegram_alerts=False,
            mt5_integration=False,
            api_access=False,
            priority_support=False,
            is_active=True
        ),
        Plan(
            name="Pro Trader",
            code="PRO",
            description="Full AI council intelligence, instant Telegram alerts & unlocked levels",
            price_monthly=49.0,
            price_yearly=470.0,
            max_signals_per_day=20,
            max_ai_analyses_per_day=50,
            telegram_alerts=True,
            mt5_integration=False,
            api_access=False,
            priority_support=True,
            is_active=True
        ),
        Plan(
            name="VIP Automated",
            code="VIP",
            description="MT5 Bridge execution, automated risk guard & priority server routing",
            price_monthly=99.0,
            price_yearly=950.0,
            max_signals_per_day=50,
            max_ai_analyses_per_day=150,
            telegram_alerts=True,
            mt5_integration=True,
            api_access=True,
            priority_support=True,
            is_active=True
        ),
        Plan(
            name="Institutional Premium",
            code="PREMIUM",
            description="Full API access, Model Context Protocol (MCP) server & dedicated analyst feeds",
            price_monthly=199.0,
            price_yearly=1890.0,
            max_signals_per_day=999,
            max_ai_analyses_per_day=999,
            telegram_alerts=True,
            mt5_integration=True,
            api_access=True,
            priority_support=True,
            is_active=True
        )
    ]
    db.add_all(plans)
    db.commit()

    # 3. Seed Users (Demo User & Admin)
    demo_user = User(
        full_name="Demo Trader (Development)",
        username="demotrader",
        email="demo@example.com",
        password_hash=get_password_hash("ChangeMe123!"),
        country="United States",
        phone="+1 555 019 2834",
        telegram_username="demotrader_mta",
        role="USER",
        is_active=True
    )
    admin_user = User(
        full_name="Chief Quant Admin",
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("AdminPass123!"),
        country="United States",
        phone="+1 555 010 8821",
        telegram_username="mta_chief_admin",
        role="ADMIN",
        is_active=True
    )
    db.add_all([demo_user, admin_user])
    db.commit()

    # Assign PRO plan to demo user and PREMIUM to admin
    pro_plan = db.query(Plan).filter(Plan.code == "PRO").first()
    prem_plan = db.query(Plan).filter(Plan.code == "PREMIUM").first()

    now = datetime.datetime.utcnow()
    db.add_all([
        Subscription(user_id=demo_user.id, plan_id=pro_plan.id, status="ACTIVE", started_at=now, expires_at=now + datetime.timedelta(days=365)),
        Subscription(user_id=admin_user.id, plan_id=prem_plan.id, status="ACTIVE", started_at=now, expires_at=now + datetime.timedelta(days=730)),
    ])
    db.commit()

    # 4. Seed Supported Assets
    assets = [
        Asset(symbol="XAUUSD", name="Gold / US Dollar", market_type="commodity", base_currency="XAU", quote_currency="USD", pip_size=0.01, precision=2),
        Asset(symbol="BTCUSDT", name="Bitcoin / Tether", market_type="crypto", base_currency="BTC", quote_currency="USDT", pip_size=0.01, precision=2),
        Asset(symbol="ETHUSDT", name="Ethereum / Tether", market_type="crypto", base_currency="ETH", quote_currency="USDT", pip_size=0.01, precision=2),
        Asset(symbol="SOLUSDT", name="Solana / Tether", market_type="crypto", base_currency="SOL", quote_currency="USDT", pip_size=0.01, precision=2),
        Asset(symbol="BNBUSDT", name="BNB / Tether", market_type="crypto", base_currency="BNB", quote_currency="USDT", pip_size=0.01, precision=2),
        Asset(symbol="EURUSD", name="Euro / US Dollar", market_type="forex", base_currency="EUR", quote_currency="USD", pip_size=0.0001, precision=4),
        Asset(symbol="GBPUSD", name="British Pound / US Dollar", market_type="forex", base_currency="GBP", quote_currency="USD", pip_size=0.0001, precision=4),
        Asset(symbol="USDJPY", name="US Dollar / Japanese Yen", market_type="forex", base_currency="USD", quote_currency="JPY", pip_size=0.01, precision=2),
        Asset(symbol="USOIL", name="Crude Oil WTI", market_type="commodity", base_currency="USOIL", quote_currency="USD", pip_size=0.01, precision=2),
        Asset(symbol="UKOIL", name="Brent Crude Oil", market_type="commodity", base_currency="UKOIL", quote_currency="USD", pip_size=0.01, precision=2),
        Asset(symbol="AAPL", name="Apple Inc.", market_type="stock", base_currency="AAPL", quote_currency="USD", pip_size=0.01, precision=2),
        Asset(symbol="TSLA", name="Tesla, Inc.", market_type="stock", base_currency="TSLA", quote_currency="USD", pip_size=0.01, precision=2),
        Asset(symbol="NVDA", name="NVIDIA Corporation", market_type="stock", base_currency="NVDA", quote_currency="USD", pip_size=0.01, precision=2),
        Asset(symbol="NAS100", name="Nasdaq 100", market_type="index", base_currency="NAS100", quote_currency="USD", pip_size=0.1, precision=2),
        Asset(symbol="US30", name="Dow Jones 30", market_type="index", base_currency="US30", quote_currency="USD", pip_size=0.1, precision=2),
    ]
    db.add_all(assets)
    db.commit()

    # 5. Seed Historical Signals and Outcomes (Last 45 days)
    symbols_pool = [
        ("XAUUSD", 2650.0, "commodity", 2),
        ("BTCUSDT", 64500.0, "crypto", 2),
        ("ETHUSDT", 3450.0, "crypto", 2),
        ("NVDA", 124.5, "stock", 2),
        ("EURUSD", 1.0850, "forex", 4),
        ("GBPUSD", 1.2940, "forex", 4),
        ("NAS100", 19800.0, "index", 2),
        ("USOIL", 74.8, "commodity", 2),
    ]

    timeframes_pool = ["15m", "1h", "4h", "1d"]
    signal_objects = []
    outcome_objects = []

    for i in range(48):
        days_ago = 45 - (i * 0.9)
        sig_date = now - datetime.timedelta(days=days_ago, hours=random.randint(1, 18))
        sym, base_p, m_type, prec = random.choice(symbols_pool)
        tf = random.choice(timeframes_pool)
        direction = "BUY" if random.random() > 0.42 else "SELL"
        
        entry = round(base_p * (1.0 + (random.uniform(-0.04, 0.04))), prec)
        dist = round(entry * (0.008 if m_type == "forex" else 0.018), prec)
        
        if direction == "BUY":
            sl = round(entry - dist, prec)
            tp1 = round(entry + (dist * 1.5), prec)
            tp2 = round(entry + (dist * 2.5), prec)
            tp3 = round(entry + (dist * 3.5), prec)
        else:
            sl = round(entry + dist, prec)
            tp1 = round(entry - (dist * 1.5), prec)
            tp2 = round(entry - (dist * 2.5), prec)
            tp3 = round(entry - (dist * 3.5), prec)

        confidence = round(random.uniform(72.0, 94.0), 1)
        is_pro = random.random() > 0.45

        # Determine outcome: ~72% win rate for institutional model demonstration
        is_win = random.random() < 0.72
        if i >= 44: # Most recent 4 are still ACTIVE
            status = "ACTIVE" if random.random() > 0.5 else "TP1_HIT"
            closed_at = None
            exit_p = None
            pnl_r = 0.0
            pnl_pct = 0.0
        else:
            if is_win:
                status = random.choice(["TP2_HIT", "TP3_HIT"])
                closed_at = sig_date + datetime.timedelta(hours=random.randint(3, 36))
                exit_p = tp2 if status == "TP2_HIT" else tp3
                pnl_r = 2.5 if status == "TP2_HIT" else 3.5
                pnl_pct = round(abs(exit_p - entry) / entry * 100.0, 2)
            else:
                status = "SL_HIT"
                closed_at = sig_date + datetime.timedelta(hours=random.randint(2, 20))
                exit_p = sl
                pnl_r = -1.0
                pnl_pct = -round(abs(sl - entry) / entry * 100.0, 2)

        sig = Signal(
            symbol=sym,
            market_type=m_type,
            timeframe=tf,
            direction=direction,
            entry=entry,
            stop_loss=sl,
            take_profit_1=tp1,
            take_profit_2=tp2,
            take_profit_3=tp3,
            confidence=confidence,
            risk_reward=2.5,
            bias="Bullish" if direction == "BUY" else "Bearish",
            technical_summary=f"Technical momentum and EMA alignment confirm {direction} setup on {tf}.",
            sentiment_summary="Macro liquidity flow and order book depth remain supportive.",
            risk_assessment="ATR buffer verified. Risk/reward ratio exceeds minimum threshold.",
            reasoning=f"High-conviction {direction} execution triggered by Multi-Agent Consensus.",
            analyst_votes_json={
                "technical": {"bias": "bullish" if direction == "BUY" else "bearish", "confidence": confidence},
                "macro": {"bias": "bullish" if direction == "BUY" else "bearish", "confidence": 75.0},
                "sentiment": {"bias": "bullish" if direction == "BUY" else "bearish", "confidence": 70.0},
                "risk": {"bias": "bullish" if direction == "BUY" else "bearish", "confidence": 85.0, "veto": False}
            },
            status=status,
            is_pro_only=is_pro,
            created_at=sig_date,
            published_at=sig_date,
            closed_at=closed_at,
            exit_price=exit_p,
            pnl_r=pnl_r,
            pnl_percentage=pnl_pct
        )
        db.add(sig)
        db.flush()

        if status in ["TP2_HIT", "TP3_HIT", "SL_HIT"]:
            outcome_objects.append(SignalOutcome(
                signal_id=sig.id,
                symbol=sym,
                outcome="WIN" if is_win else "LOSS",
                pnl_r=pnl_r,
                pnl_pct=pnl_pct,
                duration_minutes=random.randint(120, 1800),
                recorded_at=closed_at
            ))

    db.add_all(outcome_objects)
    db.commit()

    # 6. Seed News (English & Khmer)
    news_items = [
        News(
            title="Federal Reserve Signals Measured Stance as Inflation Normalizes",
            summary="FOMC meeting minutes indicate broad alignment on equilibrium interest rates with steady liquidity support for risk assets.",
            source="Institutional Macro Wire",
            language="en",
            category="Central Banks",
            impact="HIGH",
            affected_symbols_json=["XAUUSD", "EURUSD", "NAS100", "US30"],
            published_at=now - datetime.timedelta(hours=2)
        ),
        News(
            title="Bitcoin Institutional Custody Inflows Surge Past $1.8B This Week",
            summary="Sustained spot ETF volume and long-term whale accumulation push crypto market dominance to multi-month highs.",
            source="Crypto Intelligence Desk",
            language="en",
            category="Crypto",
            impact="HIGH",
            affected_symbols_json=["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            published_at=now - datetime.timedelta(hours=5)
        ),
        News(
            title="Gold Consolidates Near Record Levels Amid Central Bank Reserve Buys",
            summary="Sovereign treasury allocations into bullion maintain upward support despite brief dollar index strength.",
            source="Precious Metals Daily",
            language="en",
            category="Commodities",
            impact="HIGH",
            affected_symbols_json=["XAUUSD"],
            published_at=now - datetime.timedelta(hours=8)
        ),
        News(
            title="Tech Sector Rallies as AI Infrastructure Capex Surpasses Projections",
            summary="Semiconductor manufacturers and cloud giants report robust balance sheet expansion driving Nasdaq strength.",
            source="Equity Insight",
            language="en",
            category="Stocks",
            impact="MEDIUM",
            affected_symbols_json=["NVDA", "AAPL", "NAS100"],
            published_at=now - datetime.timedelta(hours=14)
        ),
        News(
            title="ព័ត៌មានទីផ្សារហិរញ្ញវត្ថុ៖ តម្លៃមាសបន្តកើនឡើងចំពេលធនាគារកណ្តាលទិញបង្គរ",
            summary="ទីផ្សារហិរញ្ញវត្ថុសកលបង្ហាញពីស្ថិរភាព ខណៈដែលវិនិយោគិនបន្តបង្កើនការកាន់កាប់មាស និងទ្រព្យសកម្មសុវត្ថិភាព។",
            source="Asia Financial News",
            language="km",
            category="Commodities",
            impact="HIGH",
            affected_symbols_json=["XAUUSD", "BTCUSDT"],
            published_at=now - datetime.timedelta(hours=4)
        ),
        News(
            title="បច្ចុប្បន្នភាពរូបិយប័ណ្ណឌីជីថល៖ Bitcoin រក្សាកម្រិតគាំទ្រដ៏រឹងមាំ",
            summary="លំហូរមូលនិធិស្ថាប័នចូលក្នុងទីផ្សាររូបិយប័ណ្ណគ្រីបតូ បានជំរុញឱ្យតម្លៃ Bitcoin រក្សាជំហរវិជ្ជមានជាបន្តបន្ទាប់។",
            source="Asia Financial News",
            language="km",
            category="Crypto",
            impact="HIGH",
            affected_symbols_json=["BTCUSDT", "ETHUSDT"],
            published_at=now - datetime.timedelta(hours=9)
        )
    ]
    db.add_all(news_items)
    db.commit()

    for item in news_items:
        sentiment_type = "positive" if "Surge" in item.title or "Rallies" in item.title or "កើនឡើង" in item.title or "វិជ្ជមាន" in item.title else "neutral"
        score = 0.75 if sentiment_type == "positive" else 0.1
        db.add(NewsSentiment(
            news_id=item.id,
            sentiment=sentiment_type,
            score=score,
            confidence=85.0,
            reasoning="Constructive macroeconomic wording and structural liquidity indicators."
        ))
    db.commit()

    # 7. Seed Demo User Watchlist & Journal
    db.add_all([
        Watchlist(user_id=demo_user.id, symbol="XAUUSD"),
        Watchlist(user_id=demo_user.id, symbol="BTCUSDT"),
        Watchlist(user_id=demo_user.id, symbol="NVDA"),
        Watchlist(user_id=demo_user.id, symbol="EURUSD"),
    ])

    # Sample journal entries
    db.add_all([
        TradeJournal(
            user_id=demo_user.id,
            symbol="XAUUSD",
            direction="BUY",
            timeframe="1h",
            entry_price=2648.50,
            exit_price=2682.00,
            stop_loss=2636.00,
            take_profit=2682.00,
            position_size=1.0,
            profit_loss=3350.00,
            pnl_r=2.68,
            outcome="WIN",
            notes="Followed AI Council buy consensus at support retest. Clean target reached.",
            trade_date=now - datetime.timedelta(days=3)
        ),
        TradeJournal(
            user_id=demo_user.id,
            symbol="BTCUSDT",
            direction="BUY",
            timeframe="4h",
            entry_price=63200.00,
            exit_price=65400.00,
            stop_loss=62100.00,
            take_profit=66000.00,
            position_size=0.5,
            profit_loss=1100.00,
            pnl_r=2.00,
            outcome="WIN",
            notes="Institutional breakout confirmation on 4H chart.",
            trade_date=now - datetime.timedelta(days=7)
        ),
        TradeJournal(
            user_id=demo_user.id,
            symbol="EURUSD",
            direction="SELL",
            timeframe="15m",
            entry_price=1.0880,
            exit_price=1.0895,
            stop_loss=1.0895,
            take_profit=1.0840,
            position_size=2.0,
            profit_loss=-300.00,
            pnl_r=-1.00,
            outcome="LOSS",
            notes="Stopped out during US economic release volatility spike.",
            trade_date=now - datetime.timedelta(days=10)
        )
    ])

    # 8. Seed System Logs
    db.add_all([
        SystemLog(level="INFO", module="SYSTEM", message="MyTradeAI SaaS core initialized successfully in DEMO mode."),
        SystemLog(level="INFO", module="AI_ENGINE", message="Multi-agent council consensus engine loaded with 4 specialist personas."),
        SystemLog(level="INFO", module="MARKET_DATA", message="MockMarketDataProvider active with 15 asset channels."),
    ])

    db.commit()
    db.close()
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    run_seed()
