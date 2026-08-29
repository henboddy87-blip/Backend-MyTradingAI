# MyTradeAI — Institutional AI Trading Intelligence SaaS

MyTradeAI is a local-first, full-stack **AI Trading Intelligence SaaS platform** built with **FastAPI**, **React 19**, **TypeScript**, **Tailwind CSS**, and **SQLite**. It features institutional technical analysis, quantitative market structure recognition, multi-timeframe alignment, real-time WebSocket market streaming, macroeconomic event risk modeling, a 4-agent AI Council, and automated risk management.

---

## Key Features

- **Institutional Multi-Agent AI Analyst Council**:
  - **Technical Analyst (40%)**: Trend, Momentum, Moving Averages, Volatility, Stochastics.
  - **Risk Manager (25%)**: Dynamic ATR-based Stop-Loss, S/R headroom clearance buffer, Veto safeguards.
  - **Macroeconomic Analyst (20%)**: Calendar releases (CPI, FOMC, NFP), central bank speeches.
  - **Sentiment Analyst (15%)**: Real-time news sentiment spectrum and narrative confirmation.
- **Quantitative Engine (No Hallucinations)**:
  - Technical suite: EMA (20/50/100/200), SMA (20/50/200), RSI 14, MACD, ADX, Bollinger Bands, ATR.
  - Price Action Structure: Swing Highs/Lows, Break of Structure (`BOS`), Change of Character (`CHoCH`).
  - Dynamic Regime Detection: `STRONG_TREND`, `WEAK_TREND`, `RANGE`, `BREAKOUT`, `PULLBACK`, `UNCERTAIN`.
- **Evidence-Based Confluence & Confidence Score (0–100)**:
  - Transparent 7-pillar breakdown: Trend /20, Structure /20, Momentum /15, MTF /15, News /10, Volatility /10, R:R /10.
  - Strict decision engine: `BUY`, `SELL`, or `WAIT` (capital preservation enforced).
- **Institutional Interactive Charting**:
  - Candlestick engine with volume sub-bars, crosshairs, zoom/pan, and dynamic indicator overlays (EMA, VWAP, Bollinger Bands, RSI panel, S/R, BOS levels).
- **Multi-Asset Best Setup Scanner**:
  - Continuous benchmark asset scanner (`XAUUSD`, `NAS100`, `BTCUSDT`, `EURUSD`, `ETHUSDT`, `US30`, `NVDA`, `USOIL`).
- **Audited Track Record & Mathematical Expectancy**:
  - Calculates Win Rate, Loss Rate, Profit Factor, Expected Value (EV), Max Drawdown %, and interactive equity curve.
- **Enterprise Security & Performance**:
  - Route-level code splitting & lazy loading (main bundle 282 kB).
  - In-memory indicator calculation caching with short TTL.
  - Indexed relational database queries.
  - Zero sensitive secrets exposed to client.

---

## Quick Start

### 1. Prerequisites
- **Node.js** v18+ and **npm**
- **Python** 3.11+

### 2. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # On Windows (or source venv/bin/activate on Linux/Mac)
pip install -r requirements.txt
python seed.py                  # Seeds benchmark assets, historical signals & news
python -m uvicorn app.main:app --reload --port 8000
```
- **Backend API**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **OpenAPI JSON**: `http://127.0.0.1:8000/openapi.json`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- **Frontend Dashboard**: `http://localhost:5173`

---

## Demo Credentials

All registered users receive **VIP FULL ACCESS** with unlocked signals, unlimited AI scans, and MT5 terminal bridge execution:

| Role | Username | Email | Password |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin@mytradeai.local` | `Admin123!` |
| **Trader** | `trader_demo` | `trader@mytradeai.local` | `Trader123!` |

*(Or register any new account on the registration page to automatically receive full access).*

---

## Environment Variables

Copy `.env.example` to `backend/.env`:

```env
# Application
APP_NAME=MyTradeAI
PRIMARY_DOMAIN=http://localhost:5173

# Security
SECRET_KEY=dev-secret-key-change-in-production-mytradeai-2026
JWT_SECRET_KEY=dev-jwt-secret-key-change-in-production-mytradeai-2026
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Database
DATABASE_URL=sqlite:///./data/app.db

# Operation Modes ("mock" or "live")
DATA_MODE=mock
MARKET_DATA_PROVIDER=mock
AI_PROVIDER=mock
PAYMENT_PROVIDER=mock

# Live API Providers (Optional - left blank in mock mode)
AI_API_KEY=
BINANCE_API_KEY=
TWELVEDATA_API_KEY=
TELEGRAM_BOT_TOKEN=
STRIPE_SECRET_KEY=
```

---

## Automated Test Suite

Run pytest in backend directory:
```bash
cd backend
venv\Scripts\python -m pytest tests/ -v
```
**26 of 26 tests pass** covering Indicators, Market Structure, Regime Detection, News Confirmation, Risk Engine, and Signals.

---

## Regulatory Risk Disclaimer

> **IMPORTANT**: Trading foreign exchange, cryptocurrencies, equities, and commodities on margin carries a high level of risk and may not be suitable for all investors. High leverage can work against you as well as for you. Past performance and simulated backtest results are not indicative of future results. AI analysis and quantitative signals are provided strictly for educational and informational purposes.
