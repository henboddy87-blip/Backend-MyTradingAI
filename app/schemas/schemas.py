from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, EmailStr, Field

# --- AUTH & USER SCHEMAS ---
class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    country: Optional[str] = "United States"
    phone: Optional[str] = None
    telegram_username: Optional[str] = None

class UserLogin(BaseModel):
    username_or_email: str
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    telegram_username: Optional[str] = None

class UserOut(BaseModel):
    id: int
    full_name: str
    username: str
    email: str
    country: Optional[str] = None
    phone: Optional[str] = None
    telegram_username: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    plan_code: Optional[str] = "FREE"

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)

# --- PLAN & SUBSCRIPTION SCHEMAS ---
class PlanOut(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    price_monthly: float
    price_yearly: float
    max_signals_per_day: int
    max_ai_analyses_per_day: int
    telegram_alerts: bool
    mt5_integration: bool
    api_access: bool
    priority_support: bool
    is_active: bool

    class Config:
        from_attributes = True

class SubscriptionOut(BaseModel):
    id: int
    user_id: int
    plan: PlanOut
    status: str
    started_at: datetime
    expires_at: Optional[datetime] = None
    auto_renew: bool

    class Config:
        from_attributes = True

class PaymentCreate(BaseModel):
    plan_id: int
    provider: Literal["mock", "khqr", "stripe", "crypto"] = "mock"
    billing_period: Literal["monthly", "yearly"] = "monthly"

class PaymentOut(BaseModel):
    id: int
    amount: float
    currency: str
    provider: str
    status: str
    transaction_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- API KEY SCHEMAS ---
class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    rate_limit_per_min: Optional[int] = 60

class ApiKeyCreatedResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    api_key: str # Full raw key shown ONCE
    rate_limit_per_min: int
    created_at: datetime

class ApiKeyOut(BaseModel):
    id: int
    name: str
    key_prefix: str
    rate_limit_per_min: int
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- ASSET & MARKET SCHEMAS ---
class AssetOut(BaseModel):
    id: int
    symbol: str
    name: str
    market_type: str
    base_currency: str
    quote_currency: str
    pip_size: float
    precision: int
    is_active: bool
    icon_url: Optional[str] = None

    class Config:
        from_attributes = True

class MarketCandleOut(BaseModel):
    time: int # Unix timestamp in seconds
    open: float
    high: float
    low: float
    close: float
    volume: float

class MarketTickerItem(BaseModel):
    symbol: str
    name: str
    market_type: str
    price: float
    change_24h: float
    direction: Literal["up", "down", "neutral"]
    high_24h: float
    low_24h: float
    volume_24h: float
    timestamp: datetime
    market_status: Literal["open", "closed"] = "open"

# --- TECHNICAL ANALYSIS SCHEMAS ---
class MACDResult(BaseModel):
    value: float
    signal: float
    histogram: float

class BollingerBandsResult(BaseModel):
    upper: float
    middle: float
    lower: float

class MarketStructureResult(BaseModel):
    structure_bias: Literal["BULLISH", "BEARISH", "RANGING"]
    pattern: str # e.g. "HH-HL (Bullish Structure)" or "LH-LL (Bearish Structure)"
    break_of_structure: bool
    change_of_character: bool
    swing_highs: List[float] = []
    swing_lows: List[float] = []
    recent_bos_level: Optional[float] = None
    recent_choch_level: Optional[float] = None

class MarketRegimeResult(BaseModel):
    regime: Literal["STRONG_TREND", "WEAK_TREND", "RANGE", "BREAKOUT", "PULLBACK", "HIGH_VOLATILITY", "UNCERTAIN"]
    confidence: float
    volatility_state: Literal["EXPANDING", "NORMAL", "COMPRESSING"]
    recommendation: str

class TimeframeAlignment(BaseModel):
    timeframe: str
    trend: Literal["BULLISH", "BEARISH", "NEUTRAL"]
    bias: str
    confidence: float

class MultiTimeframeSummary(BaseModel):
    alignment_score: float # 0 - 100
    alignment_state: Literal["ALIGNED_BULLISH", "ALIGNED_BEARISH", "MIXED_PULLBACK", "CONFLICT_WAIT"]
    timeframes: Dict[str, TimeframeAlignment]

class ConfidenceScoreBreakdown(BaseModel):
    trend: float = 0.0 # max 20
    structure: float = 0.0 # max 20
    momentum: float = 0.0 # max 15
    mtf: float = 0.0 # max 15
    news: float = 0.0 # max 10
    volatility: float = 0.0 # max 10
    risk_reward: float = 0.0 # max 10
    total: float = 0.0 # 0-100
    strength_tier: Literal["WEAK", "MODERATE", "HIGH", "VERY_HIGH"]

class SignalInvalidation(BaseModel):
    invalidation_price: Optional[float] = None
    invalidation_reason: str
    conditions: List[str] = []

class EconomicEventItem(BaseModel):
    title: str
    impact: Literal["HIGH", "MEDIUM", "LOW"]
    currency: str
    time_label: str
    is_approaching: bool
    risk_level: Literal["HIGH", "MODERATE", "LOW"]

class TechnicalAnalysisResult(BaseModel):
    symbol: str
    timeframe: str
    trend: Literal["bullish", "bearish", "neutral"]
    momentum: Literal["strong", "moderate", "weak"]
    rsi: float
    macd: MACDResult
    ema_20: float
    ema_50: float
    ema_200: float
    atr: float
    adx: Optional[float] = 25.0
    stochastic_k: Optional[float] = 50.0
    stochastic_d: Optional[float] = 50.0
    bollinger_bands: BollingerBandsResult
    support_levels: List[float]
    resistance_levels: List[float]
    market_structure: Optional[MarketStructureResult] = None
    market_regime: Optional[MarketRegimeResult] = None
    summary: str
    timestamp: datetime

# --- AI ANALYST COUNCIL & AI SCHEMAS ---
class AnalystVote(BaseModel):
    analyst: Literal["technical", "macro", "sentiment", "risk"]
    bias: Literal["bullish", "bearish", "neutral"]
    confidence: float
    reasoning: str
    key_levels: List[float] = []
    risk_flags: List[str] = []
    veto: bool = False

class ConsensusResult(BaseModel):
    decision: Literal["BUY", "SELL", "NO_TRADE"]
    confidence: float
    market_bias: str
    votes: Dict[str, AnalystVote]
    consensus_score: float
    vetoed_by_risk: bool = False
    reasons: List[str] = []

class AIAnalyzeRequest(BaseModel):
    symbol: str
    timeframe: str = "1h"
    risk_level: Literal["Low", "Medium", "High"] = "Medium"
    analysis_mode: Literal["Scalping", "Intraday", "Swing"] = "Intraday"
    current_price: Optional[float] = None

class AIAnalyzeResponse(BaseModel):
    symbol: str
    timeframe: str
    direction: Literal["BUY", "SELL", "NO_TRADE"]
    entry: Optional[float] = None
    entry_min: Optional[float] = None
    entry_max: Optional[float] = None
    entry_type: Literal["MARKET", "PULLBACK_LIMIT", "BREAKOUT_CONFIRMATION", "WAIT"] = "MARKET"
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    confidence: float
    risk_reward: float
    market_bias: str
    technical_analysis: Dict[str, Any]
    market_structure: Optional[MarketStructureResult] = None
    market_regime: Optional[MarketRegimeResult] = None
    mtf_alignment: Optional[MultiTimeframeSummary] = None
    confidence_breakdown: Optional[ConfidenceScoreBreakdown] = None
    invalidation: Optional[SignalInvalidation] = None
    economic_events: Optional[List[EconomicEventItem]] = None
    news_sentiment: Dict[str, Any]
    risk_assessment: str
    reasoning: str
    reasons: List[str] = []
    risks: List[str] = []
    analyst_votes: Dict[str, AnalystVote]
    timestamp: datetime
    data_mode: str = "mock"

class AIChatRequest(BaseModel):
    message: str
    symbol: Optional[str] = "XAUUSD"
    timeframe: Optional[str] = "1h"
    conversation_id: Optional[int] = None

class AIChatResponse(BaseModel):
    conversation_id: int
    reply: str
    structured_context: Optional[Dict[str, Any]] = None
    timestamp: datetime

# --- SIGNAL SCHEMAS ---
class SignalCreate(BaseModel):
    symbol: str
    market_type: str = "crypto"
    timeframe: str = "1h"
    direction: Literal["BUY", "SELL", "NO_TRADE"]
    entry: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    confidence: float = 75.0
    risk_reward: float = 2.5
    bias: str = "neutral"
    technical_summary: Optional[str] = None
    sentiment_summary: Optional[str] = None
    risk_assessment: Optional[str] = None
    reasoning: Optional[str] = None
    analyst_votes: Optional[Dict[str, Any]] = None
    is_pro_only: bool = False

class SignalUpdate(BaseModel):
    entry: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    status: Optional[str] = None
    reasoning: Optional[str] = None

class SignalOut(BaseModel):
    id: int
    symbol: str
    market_type: str
    timeframe: str
    direction: str
    entry: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    confidence: float
    risk_reward: float
    bias: str
    technical_summary: Optional[str] = None
    sentiment_summary: Optional[str] = None
    risk_assessment: Optional[str] = None
    reasoning: Optional[str] = None
    analyst_votes_json: Optional[Dict[str, Any]] = None
    status: str
    is_pro_only: bool
    is_locked_for_tier: bool = False
    created_at: datetime
    published_at: datetime
    closed_at: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl_r: float = 0.0
    pnl_percentage: float = 0.0

    class Config:
        from_attributes = True

# --- RISK SCHEMAS ---
class RiskCalculationRequest(BaseModel):
    account_balance: float = Field(..., gt=0)
    risk_percentage: float = Field(..., gt=0, le=10) # 0.1% to 10%
    entry: float = Field(..., gt=0)
    stop_loss: float = Field(..., gt=0)
    take_profit: float = Field(..., gt=0)
    symbol: str = "XAUUSD"

class RiskCalculationResponse(BaseModel):
    account_balance: float
    risk_amount: float
    reward_amount: float
    risk_reward_ratio: float
    position_size: float
    price_risk_distance: float
    price_reward_distance: float
    is_valid_risk: bool
    warnings: List[str] = []

# --- TRADE JOURNAL SCHEMAS ---
class JournalCreate(BaseModel):
    symbol: str
    direction: Literal["BUY", "SELL"]
    timeframe: str = "1h"
    entry_price: float
    exit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: float = 1.0
    profit_loss: float = 0.0
    outcome: Literal["WIN", "LOSS", "BREAKEVEN", "OPEN"] = "OPEN"
    notes: Optional[str] = None
    screenshot_url: Optional[str] = None
    tags: Optional[str] = None
    trade_date: Optional[datetime] = None

class JournalUpdate(BaseModel):
    exit_price: Optional[float] = None
    profit_loss: Optional[float] = None
    outcome: Optional[Literal["WIN", "LOSS", "BREAKEVEN", "OPEN"]] = None
    notes: Optional[str] = None
    screenshot_url: Optional[str] = None
    tags: Optional[str] = None

class JournalOut(BaseModel):
    id: int
    user_id: int
    symbol: str
    direction: str
    timeframe: str
    entry_price: float
    exit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: float
    profit_loss: float
    pnl_r: float
    outcome: str
    notes: Optional[str] = None
    screenshot_url: Optional[str] = None
    tags: Optional[str] = None
    trade_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class JournalStatsOut(BaseModel):
    total_trades: int
    wins: int
    losses: int
    breakeven: int
    open_trades: int
    win_rate: float
    total_pnl: float
    average_win: float
    average_loss: float
    profit_factor: float
    best_trade: float
    worst_trade: float

# --- WATCHLIST SCHEMAS ---
class WatchlistCreate(BaseModel):
    symbol: str

class WatchlistOut(BaseModel):
    id: int
    symbol: str
    asset_name: Optional[str] = None
    market_type: Optional[str] = None
    current_price: float = 0.0
    change_24h: float = 0.0
    ai_bias: str = "neutral"
    latest_signal: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- NEWS & SENTIMENT SCHEMAS ---
class NewsSentimentOut(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"]
    score: float
    confidence: float
    reasoning: Optional[str] = None

class NewsOut(BaseModel):
    id: int
    title: str
    summary: str
    content: Optional[str] = None
    source: str
    url: Optional[str] = None
    language: str
    category: str
    impact: str
    affected_symbols_json: List[str] = []
    published_at: datetime
    sentiment: Optional[NewsSentimentOut] = None

    class Config:
        from_attributes = True

# --- TRACK RECORD SCHEMAS ---
class EquityPoint(BaseModel):
    date: str
    equity: float
    pnl_r: float

class PerformanceByAsset(BaseModel):
    symbol: str
    trades: int
    win_rate: float
    total_r: float

class PerformanceByTimeframe(BaseModel):
    timeframe: str
    trades: int
    win_rate: float
    total_r: float

class MonthlyPerformance(BaseModel):
    month: str # e.g. "2026-05"
    pnl_pct: float
    trades: int
    win_rate: float

class TrackRecordSummaryOut(BaseModel):
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    average_r: float
    profit_factor: float
    total_r: float
    best_symbol: str
    worst_symbol: str
    equity_curve: List[EquityPoint]
    performance_by_asset: List[PerformanceByAsset]
    performance_by_timeframe: List[PerformanceByTimeframe]
    monthly_performance: List[MonthlyPerformance]
    is_demo_data: bool = True

# --- MT5 SCHEMAS ---
class Mt5AccountOut(BaseModel):
    id: int
    account_number: str
    broker: str
    server: str
    is_connected: bool
    balance: float
    equity: float
    margin: float
    free_margin: float
    live_trading_enabled: bool
    last_heartbeat: datetime

    class Config:
        from_attributes = True

class Mt5OrderOut(BaseModel):
    id: int
    symbol: str
    order_type: str
    volume: float
    open_price: float
    sl: Optional[float] = None
    tp: Optional[float] = None
    close_price: Optional[float] = None
    profit: float
    status: str
    created_at: datetime
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- MCP SCHEMAS ---
class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Any
    method: str
    params: Optional[Dict[str, Any]] = None

class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Any
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

# --- SYSTEM LOG SCHEMAS ---
class SystemLogOut(BaseModel):
    id: int
    level: str
    module: str
    message: str
    request_id: Optional[str] = None
    latency_ms: Optional[float] = None
    details_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
