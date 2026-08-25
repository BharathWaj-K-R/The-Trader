# The-Trader

A **paper-only, self-improving algorithmic trading research platform**. It is designed around validated market data, explicit risk controls, reproducible backtesting, measurable goals, persistence, controlled strategy experimentation, walk-forward validation, and restart-safe paper execution.

## Architecture

```text
                         ┌──────────────────┐
                         │  Market Data API  │
                         └────────┬─────────┘
                                  ↓
                         Validation / Sanity
                                  ↓
                         Strategy + Risk Guard
                                  ↓
                         ┌────────┴─────────┐
                         ↓                  ↓
                    Backtesting       Paper Engine
                         ↓                  ↓
                    Goal Scoring       SQLite State
                         ↓
                One-variable Experiments
                         ↓
                Candidate Backtest
                         ↓
                 Walk-forward Check
                         ↓
              Accept / Reject Baseline
```

## What is implemented

### Data and execution

- Binance public OHLCV ingestion through `ccxt`
- timestamp/order/OHLC/volume validation
- deterministic SMA + RSI strategy
- paper broker with fees and slippage
- average-cost accounting
- realized P&L
- position sizing limits
- maximum drawdown guardrail
- daily-loss guardrail with date-aware reset
- persistent paper-account state in SQLite
- explicit paper-only safety boundary

### Research

- historical backtesting
- measurable objective using return, drawdown, volatility-like risk, trade count and risk violations
- portfolio analytics including win rate and profit factor
- scientific-method optimizer that changes one strategy parameter at a time
- deterministic optimizer seed for repeatable experiments
- persisted experiment ledger
- strategy version history
- walk-forward / out-of-sample validation
- research-report persistence

### Product

- FastAPI service
- Swagger UI at `/docs`
- browser research dashboard at `/`
- CLI runner
- health and status endpoints
- Dockerfile and Docker Compose
- GitHub Actions CI running `pytest -q`

## Local setup

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

## CLI

Backtest:

```bash
python -m app.cli backtest --symbol BTC/USDT --timeframe 30m --bars 500
```

Self-improvement:

```bash
python -m app.cli improve --symbol BTC/USDT --timeframe 30m --bars 700 --cycles 10
```

## API

- `GET /health`
- `GET /api/status`
- `GET /api/trades`
- `GET /api/experiments`
- `GET /api/runs`
- `GET /api/reports`
- `POST /api/backtest`
- `POST /api/improve`
- `POST /api/walk-forward`
- `POST /api/paper/tick`
- `POST /api/paper/reset`

## Operating model

### Research mode

Backtests answer: “How did this strategy behave on this historical sample, including fees, slippage and risk constraints?”

### Improvement mode

The optimizer establishes a baseline, changes **one** parameter, evaluates the candidate, and accepts it only when the objective score improves. The experiment is stored so the reasoning remains auditable.

### Walk-forward mode

Walk-forward validation avoids treating the same historical segment as both the tuning set and the final judge. Earlier data is used for controlled optimization and later unseen data is used for evaluation. The report includes per-fold scores, returns, drawdowns and a robustness flag.

### Paper mode

`/api/paper/tick` fetches fresh market data, evaluates the current strategy, applies risk limits, simulates execution, and persists the account state. Restarting the process does not erase the paper account.

## Configuration

Copy `.env.example` to `.env`. Keep:

```text
PAPER_ONLY=true
```

The project intentionally does not include live-money order submission.

## Safety boundary

This is a **research and paper-trading platform**, not a guarantee of profitability. Historical results can overfit and can fail in live markets. There is no leverage, withdrawal functionality, or live exchange order endpoint.

## Verification

GitHub Actions runs the automated test suite on pushes and pull requests. The suite covers API behavior, broker accounting, risk limits, strategy logic, goals, optimizer behavior, walk-forward validation, and paper-account persistence.

A local environment still needs to run the suite and exercise the public market-data adapter before treating a deployment as verified. The codebase does not fabricate verification results when the execution environment cannot reach external services.

## Next hardening stage

The strongest remaining engineering work for a future production system would be an isolated exchange execution adapter, secrets management, durable scheduling/worker infrastructure, observability and alerting, stronger reconciliation, multi-asset portfolio accounting, broader walk-forward grids, transaction-cost sensitivity analysis, and a dedicated live-execution safety gate. Those are deliberately separate from this paper-only core.
