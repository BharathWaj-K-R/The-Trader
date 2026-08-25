# The-Trader

A **paper-only, self-improving algorithmic trading research platform** designed around validated market data, explicit risk controls, benchmark-relative scoring, reproducible experiments, walk-forward validation, persistent paper execution, and production-oriented operational safeguards.

The project follows a full audit-to-finish engineering process: audit, understand, repair, complete, integrate, test, harden, improve, re-engineer, re-test, polish, re-audit, and finalize.

## Architecture

```text
                         ┌─────────────────────┐
                         │ Public Market Data  │
                         └──────────┬──────────┘
                                    ↓
                           Validation / Quality
                                    ↓
                         Strategy + Risk Policy
                                    ↓
                   ┌────────────────┴────────────────┐
                   ↓                                 ↓
              Backtesting                       Paper Engine
                   ↓                                 ↓
             Goal Scoring                       SQLite State
                   ↓                                 ↓
          One-variable Experiments           Scheduler / Daemon
                   ↓
            Candidate Evaluation
                   ↓
          Walk-forward Validation
                   ↓
        Benchmark / Robustness Gate
                   ↓
          Strategy Promotion / Reject
```

## Operating modes

### Research
Backtests include trading fees, simulated slippage, risk limits, protective exits, benchmark performance, and experiment metadata.

### Improvement
The optimizer changes one strategy parameter at a time. A candidate must first improve the objective and then pass an out-of-sample walk-forward robustness gate before it becomes the active strategy.

### Walk-forward
Historical data is split into expanding training windows and unseen evaluation windows. The report contains fold-level scores, returns, drawdowns, trade counts, and a robustness decision.

### Paper execution
`/api/paper/tick` evaluates fresh market data, applies the active strategy and protective policy, simulates orders, and persists the account. The system survives restarts because account state and active strategy versions live in SQLite.

### Continuous paper mode
`python -m app.cli daemon` runs a dependency-free scheduler. Docker Compose includes a separate `paper-scheduler` service so API and execution loops can be restarted independently.

## Implemented capabilities

### Data
- Binance public OHLCV adapter through `ccxt`
- timestamp/order/OHLC/volume sanity checks
- explicit insufficient-data handling

### Strategy
- deterministic SMA + RSI momentum strategy
- persisted active strategy version
- deterministic optimization seed

### Risk
- maximum position fraction
- date-aware daily loss limit
- maximum portfolio drawdown
- stop-loss policy
- take-profit policy
- maximum holding period support
- cooldown support
- automatic paper halt on drawdown breach

### Accounting
- average-cost basis
- realized P&L
- unrealized P&L
- cash / asset / equity tracking
- restart-safe paper account

### Research quality
- total strategy return
- buy-and-hold benchmark return
- excess return versus benchmark
- maximum drawdown
- volatility-like measure
- win rate
- profit factor
- Sharpe-like reward/risk
- risk-violation count
- persisted experiment ledger
- persisted research reports

### Service
- FastAPI API
- Swagger UI at `/docs`
- browser dashboard at `/`
- `/health` liveness endpoint
- `/ready` database readiness endpoint
- protected private endpoints in production via `X-API-Key`
- CLI
- scheduler daemon
- Docker
- Docker Compose
- GitHub Actions CI

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
python -m app.cli backtest --symbol BTC/USDT --timeframe 30m --bars 700
```

Self-improvement:

```bash
python -m app.cli improve --symbol BTC/USDT --timeframe 30m --bars 700 --cycles 10
```

Walk-forward validation:

```bash
python -m app.cli walk-forward --symbol BTC/USDT --timeframe 30m --bars 700 --folds 4 --cycles 6
```

Continuous paper mode:

```bash
python -m app.cli daemon
```

## API

- `GET /health`
- `GET /ready`
- `GET /api/status`
- `GET /api/config`
- `GET /api/trades`
- `GET /api/experiments`
- `GET /api/runs`
- `GET /api/reports`
- `POST /api/backtest`
- `POST /api/improve`
- `POST /api/walk-forward`
- `POST /api/paper/tick`
- `POST /api/paper/reset`

In `production`, private endpoints require the configured `API_KEY` through the `X-API-Key` header.

## Configuration

Copy `.env.example` to `.env`.

Important controls include:

```text
PAPER_ONLY=true
INITIAL_CAPITAL=10000
MAX_POSITION_FRACTION=0.20
MAX_DAILY_LOSS_FRACTION=0.02
MAX_DRAWDOWN_FRACTION=0.10
STOP_LOSS_FRACTION=0.03
TAKE_PROFIT_FRACTION=0.06
MAX_HOLDING_BARS=0
COOLDOWN_BARS=0
ENVIRONMENT=development
API_KEY=
SCHEDULER_INTERVAL_SECONDS=300
```

`ENVIRONMENT=production` requires `API_KEY` and still keeps the system paper-only.

## Verification

GitHub Actions runs `pip install -r requirements.txt` followed by `pytest -q` on repository changes. The suite covers API behavior, readiness, accounting, daily-risk semantics, strategy behavior, objective scoring, optimizer behavior, walk-forward logic, storage persistence, protective policy, and paper state.

The system does not claim successful external-market verification when an execution environment cannot reach the upstream exchange. CI is the authoritative repository test path; live market-data validation still depends on the target runtime network.

## Safety boundary

This repository intentionally contains **no live-money order submission, leverage, withdrawals, or exchange credential workflow**. A strong backtest is not evidence of guaranteed future profitability. The paper system is the proving ground for research quality, accounting correctness, operational reliability, and experiment discipline before any separate live-execution project is considered.

## Deployment shape

```text
trader API
    |
    +---- SQLite volume
    |
    +---- dashboard / docs

paper-scheduler
    |
    +---- same SQLite volume
    +---- active strategy
    +---- persistent paper account
```

Run both services with:

```bash
docker compose up --build
```

## Remaining frontier

A future live-capable system would need an isolated execution service, exchange-specific authentication, idempotent order/reconciliation logic, secrets management, monitoring and alerting, multi-asset portfolio accounting, stronger transaction-cost stress testing, and explicit human-controlled promotion into live execution. Those remain outside this paper-only safety boundary by design.
