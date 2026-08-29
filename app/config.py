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
    DATA_MODE: str = "mock" # "mock" or "live"
    
    # AI Provider
    AI_PROVIDER: str = "mock" # "mock" or "openai"
    AI_MODEL: str = "gpt-4o-mini"
    AI_BASE_URL: str = "https://api.openai.com/v1"
    AI_API_KEY: str = ""
    
    # Market Data Provider
    MARKET_DATA_PROVIDER: str = "mock" # "mock", "binance", "twelvedata", "yahoo"
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

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
