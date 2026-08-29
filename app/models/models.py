import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON, Enum
)
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    country = Column(String(50), nullable=True, default="United States")
    phone = Column(String(30), nullable=True)
    telegram_username = Column(String(50), nullable=True)
    role = Column(String(20), default="USER", nullable=False) # USER, ADMIN
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

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

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False) # Free, Pro, VIP, Premium
    code = Column(String(20), unique=True, nullable=False) # FREE, PRO, VIP, PREMIUM
    description = Column(String(255), nullable=True)
    price_monthly = Column(Float, default=0.0)
    price_yearly = Column(Float, default=0.0)
    max_signals_per_day = Column(Integer, default=3)
    max_ai_analyses_per_day = Column(Integer, default=5)
    telegram_alerts = Column(Boolean, default=False)
    mt5_integration = Column(Boolean, default=False)
    api_access = Column(Boolean, default=False)
    priority_support = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    status = Column(String(20), default="ACTIVE") # ACTIVE, EXPIRED, CANCELLED
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    auto_renew = Column(Boolean, default=True)

    user = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    provider = Column(String(20), default="mock") # mock, khqr, stripe, crypto
    status = Column(String(20), default="PENDING") # PENDING, COMPLETED, FAILED
    transaction_id = Column(String(100), unique=True, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key_prefix = Column(String(30), nullable=False)
    key_hash = Column(String(128), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    rate_limit_per_min = Column(Integer, default=60)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="api_keys")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    market_type = Column(String(30), nullable=False) # crypto, forex, commodity, stock, index
    base_currency = Column(String(10), nullable=False)
    quote_currency = Column(String(10), nullable=False)
    pip_size = Column(Float, default=0.0001)
    precision = Column(Integer, default=4)
    min_lot = Column(Float, default=0.01)
    max_lot = Column(Float, default=100.0)
    is_active = Column(Boolean, default=True)
    icon_url = Column(String(255), nullable=True)


class MarketCandle(Base):
    __tablename__ = "market_candles"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    timeframe = Column(String(10), index=True, nullable=False) # 1m, 5m, 15m, 30m, 1h, 4h, 1d
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, default=0.0)
    timestamp = Column(DateTime, index=True, default=datetime.datetime.utcnow)


class TechnicalAnalysis(Base):
    __tablename__ = "technical_analyses"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    timeframe = Column(String(10), index=True, nullable=False)
    trend = Column(String(20), default="neutral") # bullish, bearish, neutral
    momentum = Column(String(20), default="moderate") # strong, moderate, weak
    rsi = Column(Float, nullable=False)
    macd_value = Column(Float, nullable=False)
    macd_signal = Column(Float, nullable=False)
    macd_hist = Column(Float, nullable=False)
    ema_20 = Column(Float, nullable=False)
    ema_50 = Column(Float, nullable=False)
    ema_200 = Column(Float, nullable=False)
    atr = Column(Float, nullable=False)
    bb_upper = Column(Float, nullable=False)
    bb_middle = Column(Float, nullable=False)
    bb_lower = Column(Float, nullable=False)
    support_levels_json = Column(JSON, default=list)
    resistance_levels_json = Column(JSON, default=list)
    summary = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    content = Column(Text, nullable=True)
    source = Column(String(100), default="Financial Wire")
    url = Column(String(255), nullable=True)
    language = Column(String(10), default="en", index=True) # en, km
    category = Column(String(50), default="General", index=True) # Crypto, Forex, Commodities, Central Banks
    impact = Column(String(20), default="MEDIUM", index=True) # HIGH, MEDIUM, LOW
    affected_symbols_json = Column(JSON, default=list)
    published_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    sentiment = relationship("NewsSentiment", back_populates="news", uselist=False, cascade="all, delete-orphan")


class NewsSentiment(Base):
    __tablename__ = "news_sentiments"

    id = Column(Integer, primary_key=True, index=True)
    news_id = Column(Integer, ForeignKey("news.id", ondelete="CASCADE"), nullable=False, index=True)
    sentiment = Column(String(20), default="neutral") # positive, negative, neutral
    score = Column(Float, default=0.0) # -1.0 to 1.0
    confidence = Column(Float, default=70.0) # 0 to 100
    reasoning = Column(Text, nullable=True)

    news = relationship("News", back_populates="sentiment")


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    market_type = Column(String(30), default="crypto")
    timeframe = Column(String(10), default="1h", index=True)
    direction = Column(String(10), nullable=False, index=True) # BUY, SELL, NO_TRADE
    entry = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit_1 = Column(Float, nullable=True)
    take_profit_2 = Column(Float, nullable=True)
    take_profit_3 = Column(Float, nullable=True)
    confidence = Column(Float, default=0.0, index=True)
    risk_reward = Column(Float, default=0.0)
    bias = Column(String(20), default="neutral")
    technical_summary = Column(Text, nullable=True)
    sentiment_summary = Column(Text, nullable=True)
    risk_assessment = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)
    analyst_votes_json = Column(JSON, default=dict)
    status = Column(String(20), default="ACTIVE", index=True) # ACTIVE, TP1_HIT, TP2_HIT, TP3_HIT, SL_HIT, EXPIRED, CANCELLED, NO_TRADE
    is_pro_only = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    published_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    closed_at = Column(DateTime, nullable=True)
    exit_price = Column(Float, nullable=True)
    pnl_r = Column(Float, default=0.0)
    pnl_percentage = Column(Float, default=0.0)

    outcomes = relationship("SignalOutcome", back_populates="signal", cascade="all, delete-orphan")


class SignalOutcome(Base):
    __tablename__ = "signal_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("signals.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    outcome = Column(String(20), nullable=False, index=True) # WIN, LOSS, BREAKEVEN, EXPIRED, CANCELLED
    pnl_r = Column(Float, default=0.0)
    pnl_pct = Column(Float, default=0.0)
    duration_minutes = Column(Integer, default=0)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    signal = relationship("Signal", back_populates="outcomes")


class TradeJournal(Base):
    __tablename__ = "trade_journals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    direction = Column(String(10), nullable=False) # BUY, SELL
    timeframe = Column(String(10), default="1h")
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    position_size = Column(Float, default=1.0)
    profit_loss = Column(Float, default=0.0)
    pnl_r = Column(Float, default=0.0)
    outcome = Column(String(20), default="OPEN") # WIN, LOSS, BREAKEVEN, OPEN
    notes = Column(Text, nullable=True)
    screenshot_url = Column(String(255), nullable=True)
    tags = Column(String(100), nullable=True)
    trade_date = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="journal_entries")


class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="watchlist_items")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(30), default="SIGNAL") # SIGNAL, SYSTEM, ALERT, RISK
    is_read = Column(Boolean, default=False)
    data_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class TelegramAccount(Base):
    __tablename__ = "telegram_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    chat_id = Column(String(50), nullable=True)
    telegram_username = Column(String(50), nullable=True)
    is_verified = Column(Boolean, default=False)
    notifications_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="telegram_account")


class Mt5Account(Base):
    __tablename__ = "mt5_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    account_number = Column(String(50), nullable=False)
    broker = Column(String(100), default="MetaQuotes-Demo")
    server = Column(String(100), default="Demo-Server")
    is_connected = Column(Boolean, default=True)
    balance = Column(Float, default=10000.0)
    equity = Column(Float, default=10000.0)
    margin = Column(Float, default=0.0)
    free_margin = Column(Float, default=10000.0)
    live_trading_enabled = Column(Boolean, default=False)
    last_heartbeat = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="mt5_accounts")
    orders = relationship("Mt5Order", back_populates="account", cascade="all, delete-orphan")


class Mt5Order(Base):
    __tablename__ = "mt5_orders"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("mt5_accounts.id", ondelete="CASCADE"), nullable=False)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=True)
    symbol = Column(String(20), nullable=False)
    order_type = Column(String(10), nullable=False) # BUY, SELL
    volume = Column(Float, default=0.1)
    open_price = Column(Float, nullable=False)
    sl = Column(Float, nullable=True)
    tp = Column(Float, nullable=True)
    close_price = Column(Float, nullable=True)
    profit = Column(Float, default=0.0)
    status = Column(String(20), default="OPEN") # PENDING, OPEN, CLOSED, REJECTED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

    account = relationship("Mt5Account", back_populates="orders")


class AiConversation(Base):
    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(150), default="Trading Analysis Session")
    symbol = Column(String(20), nullable=True)
    timeframe = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="ai_conversations")
    messages = relationship("AiMessage", back_populates="conversation", cascade="all, delete-orphan")


class AiMessage(Base):
    __tablename__ = "ai_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String(20), nullable=False) # USER, ASSISTANT, SYSTEM
    content = Column(Text, nullable=False)
    structured_data_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("AiConversation", back_populates="messages")


class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    summary = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(100), default="MyTradeAI Research Desk")
    cover_image = Column(String(255), nullable=True)
    is_published = Column(Boolean, default=True)
    published_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    cert_number = Column(String(50), unique=True, nullable=False)
    issue_date = Column(DateTime, default=datetime.datetime.utcnow)
    track_record_summary_json = Column(JSON, nullable=True)
    qr_code_url = Column(String(255), nullable=True)

    user = relationship("User", back_populates="certificates")


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), default="INFO") # INFO, WARNING, ERROR, AUDIT
    module = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    request_id = Column(String(50), nullable=True)
    user_id = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)
    details_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
