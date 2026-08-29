from apscheduler.schedulers.background import BackgroundScheduler
from app.core.database import SessionLocal
from app.services.signal_engine import SignalEngine
from app.models.models import Signal
from app.core.logging import logger

scheduler = BackgroundScheduler()

def job_evaluate_signals():
    db = SessionLocal()
    try:
        SignalEngine.evaluate_active_signals(db)
    except Exception as e:
        logger.error(f"Error in background signal evaluation: {e}")
    finally:
        db.close()

def job_auto_scan_market():
    """
    Autonomous background scanner: Continuously evaluates live markets
    and auto-generates signals whenever high-confidence setups form.
    """
    db = SessionLocal()
    try:
        active_count = db.query(Signal).filter(Signal.status.in_(["ACTIVE", "TP1_HIT", "TP2_HIT"])).count()
        if active_count < 15:
            # Auto-generate 3-5 fresh verified signals
            SignalEngine.auto_scan_and_generate_signals(db, target_count=3)
    except Exception as e:
        logger.error(f"Error in autonomous background market scan: {e}")
    finally:
        db.close()

def start_background_scheduler():
    try:
        # Run signal lifecycle check every 30 seconds
        scheduler.add_job(job_evaluate_signals, "interval", seconds=30, id="signal_evaluator", replace_existing=True)
        # Run autonomous market strategy scan every 60 seconds
        scheduler.add_job(job_auto_scan_market, "interval", seconds=60, id="market_auto_scanner", replace_existing=True)
        scheduler.start()
        logger.info("APScheduler background tasks initialized (Signal Evaluator + Autonomous Market Scanner).")
    except Exception as e:
        logger.error(f"Failed to start APScheduler: {e}")

def shutdown_background_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler background tasks shut down.")
