# The-Trader

A **paper-only, self-improving algorithmic trading research agent**. The repository started as an empty shell containing only this README; the implementation has now been built around validated market data, explicit risk controls, backtesting, measurable goals, persistence, and a scientific-method optimization loop.

## What it does

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
- max-position, daily-loss and drawdown guardrails
- backtesting engine
- measurable objective including return, drawdown, Sharpe-like reward/risk, trade count and risk violations
- SQLite persistence for runs, trades, experiments and strategy versions
- scientific-method optimizer that changes one parameter at a time
- automatic baseline promotion only when the candidate score improves
- FastAPI service with health/status/diagnostic/backtest/improvement endpoints
- CLI runner
- pytest coverage for core strategy/risk/goal/optimizer behavior
- Docker and Docker Compose configuration

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

Open `http://127.0.0.1:8000`.

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

Open `/docs` for the interactive FastAPI Swagger UI.

## Configuration

Copy `.env.example` to `.env` and adjust the values. `PAPER_ONLY=true` is intentional and should remain enabled for this repository unless a separately designed and reviewed live-execution layer is introduced.

## Self-improvement design

The optimizer starts with a baseline strategy and performs controlled experiments. Each candidate changes **one parameter only**. A candidate is accepted only when its measurable score is better than the current baseline. All experiments are persisted so the learning history survives process restarts.

This is deliberately not an unconstrained machine-learning system. The improvement process is bounded, reproducible in its evaluation logic, and protected by risk limits.

## Important limitation

This project is a **research and paper-trading system**. A good historical backtest does not prove future profitability. There is no live-money order API, leverage, withdrawal functionality, or promise of returns.

## Production-hardening roadmap

The core research loop is implemented. A production system would still need exchange-specific execution adapters, secrets management, stronger portfolio accounting, durable task scheduling, monitoring/alerting, walk-forward validation, transaction-level reconciliation, and a full end-to-end deployment test against the target infrastructure.
