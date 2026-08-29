import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="United States")
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    telegram_username: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="USER", nullable=False) # USER, ADMIN
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    journal_entries = relationship("TradeJournal", back_populates="user", cascade="all, delete-orphan")
    watchlist_items = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    telegram_account = relationship("TelegramAccount", back_populates="user", uselist=False, cascade="all, delete-orphan")
    mt5_accounts = relationship("Mt5Account", back_populates="user", cascade="all, delete-orphan")
    ai_conversations = relationship("AiConversation", back_populates="user", cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="user", cascade="all, delete-orphan")


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False) # Free, Pro, VIP, Premium
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False) # FREE, PRO, VIP, PREMIUM
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    price_monthly: Mapped[float] = mapped_column(Float, default=0.0)
    price_yearly: Mapped[float] = mapped_column(Float, default=0.0)
    max_signals_per_day: Mapped[int] = mapped_column(Integer, default=3)
    max_ai_analyses_per_day: Mapped[int] = mapped_column(Integer, default=5)
    telegram_alerts: Mapped[bool] = mapped_column(Boolean, default=False)
    mt5_integration: Mapped[bool] = mapped_column(Boolean, default=False)
    api_access: Mapped[bool] = mapped_column(Boolean, default=False)
    priority_support: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("plans.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE") # ACTIVE, EXPIRED, CANCELLED
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)

    user = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("plans.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    provider: Mapped[str] = mapped_column(String(20), default="mock") # mock, khqr, stripe, crypto
    status: Mapped[str] = mapped_column(String(20), default="PENDING") # PENDING, COMPLETED, FAILED
    transaction_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    metadata_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(30), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    rate_limit_per_min: Mapped[int] = mapped_column(Integer, default=60)
    expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    last_used_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)

    user = relationship("User", back_populates="api_keys")


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    market_type: Mapped[str] = mapped_column(String(30), nullable=False) # crypto, forex, commodity, stock, index
    base_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    quote_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    pip_size: Mapped[float] = mapped_column(Float, default=0.0001)
    precision: Mapped[int] = mapped_column(Integer, default=4)
    min_lot: Mapped[float] = mapped_column(Float, default=0.01)
    max_lot: Mapped[float] = mapped_column(Float, default=100.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    icon_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class MarketCandle(Base):
    __tablename__ = "market_candles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), index=True, nullable=False) # 1m, 5m, 15m, 30m, 1h, 4h, 1d
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime, index=True, default=datetime.datetime.utcnow)


class TechnicalAnalysis(Base):
    __tablename__ = "technical_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    trend: Mapped[str] = mapped_column(String(20), default="neutral") # bullish, bearish, neutral
    momentum: Mapped[str] = mapped_column(String(20), default="moderate") # strong, moderate, weak
    rsi: Mapped[float] = mapped_column(Float, nullable=False)
    macd_value: Mapped[float] = mapped_column(Float, nullable=False)
    macd_signal: Mapped[float] = mapped_column(Float, nullable=False)
    macd_hist: Mapped[float] = mapped_column(Float, nullable=False)
    ema_20: Mapped[float] = mapped_column(Float, nullable=False)
    ema_50: Mapped[float] = mapped_column(Float, nullable=False)
    ema_200: Mapped[float] = mapped_column(Float, nullable=False)
    atr: Mapped[float] = mapped_column(Float, nullable=False)
    bb_upper: Mapped[float] = mapped_column(Float, nullable=False)
    bb_middle: Mapped[float] = mapped_column(Float, nullable=False)
    bb_lower: Mapped[float] = mapped_column(Float, nullable=False)
    support_levels_json: Mapped[Any] = mapped_column(JSON, default=list)
    resistance_levels_json: Mapped[Any] = mapped_column(JSON, default=list)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class News(Base):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(100), default="Financial Wire")
    url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en", index=True) # en, km
    category: Mapped[str] = mapped_column(String(50), default="General", index=True) # Crypto, Forex, Commodities, Central Banks
    impact: Mapped[str] = mapped_column(String(20), default="MEDIUM", index=True) # HIGH, MEDIUM, LOW
    affected_symbols_json: Mapped[Any] = mapped_column(JSON, default=list)
    published_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, index=True)

    sentiment = relationship("NewsSentiment", back_populates="news", uselist=False, cascade="all, delete-orphan")


class NewsSentiment(Base):
    __tablename__ = "news_sentiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    news_id: Mapped[int] = mapped_column(Integer, ForeignKey("news.id", ondelete="CASCADE"), nullable=False, index=True)
    sentiment: Mapped[str] = mapped_column(String(20), default="neutral") # positive, negative, neutral
    score: Mapped[float] = mapped_column(Float, default=0.0) # -1.0 to 1.0
    confidence: Mapped[float] = mapped_column(Float, default=70.0) # 0 to 100
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    news = relationship("News", back_populates="sentiment")


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    market_type: Mapped[str] = mapped_column(String(30), default="crypto")
    timeframe: Mapped[str] = mapped_column(String(10), default="1h", index=True)
    direction: Mapped[str] = mapped_column(String(10), nullable=False, index=True) # BUY, SELL, NO_TRADE
    entry: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stop_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    take_profit_1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    take_profit_2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    take_profit_3: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    risk_reward: Mapped[float] = mapped_column(Float, default=0.0)
    bias: Mapped[str] = mapped_column(String(20), default="neutral")
    technical_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sentiment_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risk_assessment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    analyst_votes_json: Mapped[Any] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", index=True) # ACTIVE, TP1_HIT, TP2_HIT, TP3_HIT, SL_HIT, EXPIRED, CANCELLED, NO_TRADE
    is_pro_only: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, index=True)
    published_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, index=True)
    closed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    exit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pnl_r: Mapped[float] = mapped_column(Float, default=0.0)
    pnl_percentage: Mapped[float] = mapped_column(Float, default=0.0)

    outcomes = relationship("SignalOutcome", back_populates="signal", cascade="all, delete-orphan")


class SignalOutcome(Base):
    __tablename__ = "signal_outcomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    signal_id: Mapped[int] = mapped_column(Integer, ForeignKey("signals.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    outcome: Mapped[str] = mapped_column(String(20), nullable=False, index=True) # WIN, LOSS, BREAKEVEN, EXPIRED, CANCELLED
    pnl_r: Mapped[float] = mapped_column(Float, default=0.0)
    pnl_pct: Mapped[float] = mapped_column(Float, default=0.0)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    recorded_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, index=True)

    signal = relationship("Signal", back_populates="outcomes")


class TradeJournal(Base):
    __tablename__ = "trade_journals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(10), nullable=False) # BUY, SELL
    timeframe: Mapped[str] = mapped_column(String(10), default="1h")
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    exit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stop_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    take_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    position_size: Mapped[float] = mapped_column(Float, default=1.0)
    profit_loss: Mapped[float] = mapped_column(Float, default=0.0)
    pnl_r: Mapped[float] = mapped_column(Float, default=0.0)
    outcome: Mapped[str] = mapped_column(String(20), default="OPEN") # WIN, LOSS, BREAKEVEN, OPEN
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    screenshot_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    trade_date: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="journal_entries")


class Watchlist(Base):
    __tablename__ = "watchlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="watchlist_items")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(30), default="SIGNAL") # SIGNAL, SYSTEM, ALERT, RISK
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    data_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class TelegramAccount(Base):
    __tablename__ = "telegram_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    chat_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    telegram_username: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="telegram_account")


class Mt5Account(Base):
    __tablename__ = "mt5_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    account_number: Mapped[str] = mapped_column(String(50), nullable=False)
    broker: Mapped[str] = mapped_column(String(100), default="MetaQuotes-Demo")
    server: Mapped[str] = mapped_column(String(100), default="Demo-Server")
    is_connected: Mapped[bool] = mapped_column(Boolean, default=True)
    balance: Mapped[float] = mapped_column(Float, default=10000.0)
    equity: Mapped[float] = mapped_column(Float, default=10000.0)
    margin: Mapped[float] = mapped_column(Float, default=0.0)
    free_margin: Mapped[float] = mapped_column(Float, default=10000.0)
    live_trading_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    last_heartbeat: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="mt5_accounts")
    orders = relationship("Mt5Order", back_populates="account", cascade="all, delete-orphan")


class Mt5Order(Base):
    __tablename__ = "mt5_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("mt5_accounts.id", ondelete="CASCADE"), nullable=False)
    signal_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("signals.id"), nullable=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    order_type: Mapped[str] = mapped_column(String(10), nullable=False) # BUY, SELL
    volume: Mapped[float] = mapped_column(Float, default=0.1)
    open_price: Mapped[float] = mapped_column(Float, nullable=False)
    sl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    close_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    profit: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="OPEN") # PENDING, OPEN, CLOSED, REJECTED
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    closed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)

    account = relationship("Mt5Account", back_populates="orders")


class AiConversation(Base):
    __tablename__ = "ai_conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(150), default="Trading Analysis Session")
    symbol: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    timeframe: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="ai_conversations")
    messages = relationship("AiMessage", back_populates="conversation", cascade="all, delete-orphan")


class AiMessage(Base):
    __tablename__ = "ai_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(Integer, ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False)
    sender: Mapped[str] = mapped_column(String(20), nullable=False) # USER, ASSISTANT, SYSTEM
    content: Mapped[str] = mapped_column(Text, nullable=False)
    structured_data_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("AiConversation", back_populates="messages")


class BlogPost(Base):
    __tablename__ = "blog_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(100), default="MyTradeAI Research Desk")
    cover_image: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    published_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    cert_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    issue_date: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    track_record_summary_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    qr_code_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    user = relationship("User", back_populates="certificates")


class SystemLog(Base):
    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    level: Mapped[str] = mapped_column(String(20), default="INFO") # INFO, WARNING, ERROR, AUDIT
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    request_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    details_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, index=True)
