import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # App & Brand Config
    APP_NAME: str = "MyTradeAI"
    APP_DESCRIPTION: str = "Institutional-Grade AI Trading Intelligence & Market Analysis"
    APP_LOGO: str = "/logo.svg"
    APP_FAVICON: str = "/favicon.ico"
    PRIMARY_DOMAIN: str = "http://localhost:5173"
    SUPPORT_EMAIL: str = "support@mytradeai.local"
    TELEGRAM_USERNAME: str = "MyTradeAIBot"
    DISCORD_URL: str = "https://discord.gg/mytradeai"
    
    # Server & Security
    SECRET_KEY: str = "dev-secret-key-change-in-production-mytradeai-2026"
    JWT_SECRET_KEY: str = "dev-jwt-secret-key-change-in-production-mytradeai-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/app.db"
    
    # Modes
    DATA_MODE: str = "live" # "mock" or "live"
    
    # AI Provider
    AI_PROVIDER: str = "mock" # "mock" or "openai"
    AI_MODEL: str = "gpt-4o-mini"
    AI_BASE_URL: str = "https://api.openai.com/v1"
    AI_API_KEY: str = ""
    
    # Market Data Provider
    MARKET_DATA_PROVIDER: str = "live" # "live", "binance", "twelvedata", "yahoo", "mock"
    BINANCE_API_KEY: str = ""
    TWELVEDATA_API_KEY: str = ""
    
    # Telegram Integration
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    
    # Payment Provider
    PAYMENT_PROVIDER: str = "mock" # "mock", "khqr", "stripe", "crypto"
    STRIPE_SECRET_KEY: str = ""
    
    # MT5 Execution Bridge
    MT5_LIVE_TRADING: bool = False

    # Centralized Signal Engine Scoring Model Configurable Weights
    WEIGHT_MARKET_STRUCTURE: float = 0.20
    WEIGHT_HTF_TREND: float = 0.15
    WEIGHT_TREND_INDICATORS: float = 0.10
    WEIGHT_MOMENTUM: float = 0.10
    WEIGHT_MULTI_TIMEFRAME: float = 0.15
    WEIGHT_SUPPORT_RESISTANCE: float = 0.10
    WEIGHT_VOLATILITY: float = 0.05
    WEIGHT_VOLUME: float = 0.05
    WEIGHT_NEWS: float = 0.05
    WEIGHT_RISK_REWARD: float = 0.05

    # Minimum Decision Thresholds
    SIGNAL_ENTRY_MIN_SCORE: float = 70.0
    SIGNAL_MIN_DIRECTIONAL_ADVANTAGE: float = 25.0

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
