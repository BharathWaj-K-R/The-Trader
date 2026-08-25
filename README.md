# The-Trader

A **paper-only, self-improving algorithmic trading research agent** built around validated market data, explicit risk controls, backtesting, measurable goals, persistence, scientific-method optimization, and a browser dashboard.

## Architecture

```text
Market Data
    ↓
Validation
    ↓
SMA + RSI Strategy
    ↓
Risk Guard
    ↓
Paper Broker
    ↓
Backtest / Trade Result
    ↓
Goal Scoring
    ↓
One-variable Experiment
    ↓
Candidate Backtest
    ↓
Better score? ── yes ──> New Baseline
      │
      └── no ──────────> Reject
```

## Current capabilities

- Binance public OHLCV ingestion through `ccxt`
- timestamp/order/OHLC/volume validation
- deterministic SMA + RSI strategy
- paper broker with fees and slippage
- average-cost accounting and realized P&L
- max-position, daily-loss and drawdown guardrails
- backtesting engine
- measurable objective including return, drawdown, Sharpe-like reward/risk, trade count and risk violations
- SQLite persistence for runs, trades, experiments and strategy versions
- scientific-method optimizer that changes one parameter at a time
- automatic baseline promotion only when the candidate score improves
- FastAPI service with health/status/diagnostic/backtest/improvement endpoints
- browser dashboard at `/`
- CLI runner
- pytest coverage for API, broker, strategy, risk, goal and optimizer behavior
- Docker and Docker Compose configuration
- GitHub Actions CI running the test suite

## Run locally

```bash
python -m venv .venv

# Windows
.venv\\Scripts\\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` for the dashboard or `/docs` for Swagger UI.

### Backtest

```bash
python -m app.cli backtest --symbol BTC/USDT --timeframe 30m --bars 300
```

### Self-improve

```bash
python -m app.cli improve --symbol BTC/USDT --timeframe 30m --bars 500 --cycles 10
```

## API

- `GET /health`
- `GET /api/status`
- `GET /api/trades`
- `GET /api/experiments`
- `GET /api/runs`
- `POST /api/backtest`
- `POST /api/improve`

## Configuration

Copy `.env.example` to `.env` and adjust the values. `PAPER_ONLY=true` is intentional.

## Self-improvement design

The optimizer starts with a baseline strategy and performs controlled experiments. Each candidate changes **one parameter only**. A candidate is accepted only when its measurable score is better than the current baseline. All experiments are persisted so the learning history survives process restarts.

## Safety boundary

This project is a **research and paper-trading system**. A good historical backtest does not prove future profitability. There is no live-money order API, leverage, withdrawal functionality, or promise of returns.

## Verification status

The repository contains an automated CI workflow that runs `pytest -q` on pushes and pull requests. In environments where external GitHub networking is unavailable, the suite cannot be honestly reported as executed locally from that environment; CI remains the authoritative execution path.

## Next hardening stage

A production-grade system would still require exchange-specific execution adapters, secrets management, durable task scheduling, monitoring/alerting, walk-forward and out-of-sample validation, transaction-level reconciliation, and a fully isolated live-execution subsystem. Those are intentionally outside this paper-only build.
