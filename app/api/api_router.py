from fastapi import APIRouter
from app.api.routes import (
    auth, market, technical, signals, ai, risk, journal,
    watchlist, news, track_record, subscriptions, api_keys,
    telegram, mt5, admin, mcp, websocket
)

api_router = APIRouter(prefix="/api/v1")

# Include v1 endpoints
api_router.include_router(auth.router)
api_router.include_router(market.router)
api_router.include_router(technical.router)
api_router.include_router(signals.router)
api_router.include_router(ai.router)
api_router.include_router(risk.router)
api_router.include_router(journal.router)
api_router.include_router(watchlist.router)
api_router.include_router(news.router)
api_router.include_router(track_record.router)
api_router.include_router(subscriptions.router)
api_router.include_router(api_keys.router)
api_router.include_router(telegram.router)
api_router.include_router(mt5.router)
api_router.include_router(admin.router)

# Model Context Protocol router (also exposed at top-level /api/mcp)
mcp_router = APIRouter(prefix="/api")
mcp_router.include_router(mcp.router)
