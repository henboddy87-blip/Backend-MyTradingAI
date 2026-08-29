import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.database import engine, Base
from app.core.logging import logger
from app.api.api_router import api_router, mcp_router
from app.services.background_scheduler import start_background_scheduler, shutdown_background_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables if not exist & start scheduler
    logger.info(f"Starting {settings.APP_NAME} SaaS Backend (Data Mode: {settings.DATA_MODE})...")
    Base.metadata.create_all(bind=engine)
    try:
        from app.models.models import User
        from app.core.database import SessionLocal
        from seed import run_seed
        _db = SessionLocal()
        if not _db.query(User).first():
            logger.info("Fresh database detected. Auto-seeding initial assets, models, and demo accounts...")
            run_seed()
        _db.close()
    except Exception as e:
        logger.warning(f"Auto-seed check note: {e}")

    start_background_scheduler()
    yield
    # Shutdown: Stop scheduler
    logger.info(f"Shutting down {settings.APP_NAME} SaaS Backend...")
    shutdown_background_scheduler()

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS
origins = settings.cors_origins_list
if not origins:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all local origins during local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Latency and Request ID middleware
@app.middleware("http")
async def add_process_time_and_id(request: Request, call_next):
    req_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    response: Response = await call_next(request)
    process_time = (time.time() - start_time) * 1000.0
    response.headers["X-Request-ID"] = req_id
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    return response

# Include Routers
app.include_router(api_router)
app.include_router(mcp_router)
from app.api.routes.websocket import router as ws_router
app.include_router(ws_router)

@app.get("/")
def root():
    return {
        "app_name": settings.APP_NAME,
        "description": settings.APP_DESCRIPTION,
        "version": "1.0.0",
        "data_mode": settings.DATA_MODE,
        "api_docs": "/docs",
        "status": "operational"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "data_mode": settings.DATA_MODE,
        "ai_provider": settings.AI_PROVIDER,
        "market_provider": settings.MARKET_DATA_PROVIDER
    }
