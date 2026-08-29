from apscheduler.schedulers.background import BackgroundScheduler
from app.core.database import SessionLocal
from app.services.signal_engine import SignalEngine
from app.services.news_service import NewsService
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
    Autonomous background scanner placeholder:
    Signal generation is on-demand based on explicit user trigger & live market analysis.
    """
    pass

def job_sync_live_news():
    """
    Background news synchronization: Fetches fresh institutional market headlines
    from live financial feeds and performs algorithmic sentiment scoring.
    """
    db = SessionLocal()
    try:
        NewsService.sync_live_news(db, max_per_feed=6)
    except Exception as e:
        logger.error(f"Error in background live news sync: {e}")
    finally:
        db.close()

def start_background_scheduler():
    try:
        # Run signal lifecycle check every 30 seconds
        scheduler.add_job(job_evaluate_signals, "interval", seconds=30, id="signal_evaluator", replace_existing=True)
        # Run live financial news sync every 5 minutes
        scheduler.add_job(job_sync_live_news, "interval", minutes=5, id="live_news_syncer", replace_existing=True)
        scheduler.start()
        logger.info("APScheduler background tasks initialized (Signal Evaluator + Live News Syncer).")
    except Exception as e:
        logger.error(f"Failed to start APScheduler: {e}")

def shutdown_background_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler background tasks shut down.")
