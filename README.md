# The-Trader

**The-Trader is a full-scale algorithmic trading platform and research engine with paper, sandbox, and live-capable spot execution modes.**

It combines validated market data, deterministic strategy logic, research/backtesting, controlled self-improvement, walk-forward validation, transaction-cost stress testing, persistent accounting, risk controls, exchange execution, reconciliation, operator controls, a web console, CLI, Docker deployment, and CI.

The engineering goal follows the project's audit protocol: **AUDIT → UNDERSTAND → REPAIR → COMPLETE → INTEGRATE → TEST → HARDEN → IMPROVE → RE-ENGINEER → RE-TEST → POLISH → RE-AUDIT → FINALIZE**.

## 1. Operating model

The system deliberately separates research from execution:

```text
                           MARKET DATA
                                |
                                v
                       DATA VALIDATION
                                |
                                v
                    STRATEGY / SIGNAL ENGINE
                                |
                         RISK / POLICY
                                |
                +---------------+---------------+
                |               |               |
                v               v               v
             PAPER          SANDBOX           LIVE
                |               |               |
                +---------------+---------------+
                                |
                                v
                         ORDER GATEWAY
                                |
                                v
                         EXCHANGE / CCXT
                                |
                                v
                     RECONCILIATION ENGINE
                                |
                                v
                       PERSISTENT LEDGER
                                |
                                v
                    DASHBOARD / API / ALERTS
```

### Paper
No exchange credentials are needed. Orders are simulated against public market data and persisted locally.

### Sandbox
The same execution gateway uses exchange sandbox/testnet mode where the selected exchange supports it. Real credentials are still required, but the target is the exchange's sandbox environment rather than the production account.

### Live
The gateway can submit spot orders to the configured exchange. Live mode is intentionally gated by credentials, `LIVE_TRADING_ENABLED=true`, a separate confirmation token, explicit arming, order-notional limits, daily order limits, and a kill switch.

There is **no leverage, withdrawals, derivatives, or transfer functionality** in this first live-capable implementation.

## 2. Why the architecture is split

The strategy engine never receives exchange credentials and never calls the exchange directly.

That means:

```text
strategy says: BUY
        |
        v
risk / execution policy decides
        |
        v
order gateway validates
        |
        v
exchange call
        |
        v
reconcile actual exchange state
```

This makes the research engine reusable and keeps execution concerns, credential handling, order limits, reconciliation and operator controls in a separate boundary.

## 3. Main capabilities

### Research

- historical backtesting
- trading fees and slippage
- buy-and-hold benchmark
- excess return
- maximum drawdown
- Sharpe-like score
- win rate
- profit factor
- risk-violation tracking
- stop-loss / take-profit
- maximum holding period
- cooldowns
- walk-forward validation
- one-variable scientific experiments
- deterministic optimizer seed
- transaction-cost sensitivity matrix
- full research orchestration
- persisted research reports
- strategy version history

### Execution

- paper execution
- exchange sandbox execution
- live spot execution
- market orders
- limit orders
- explicit order-size cap
- explicit orders-per-day cap
- exchange precision/minimum checks
- order persistence
- order status refresh
- open-order reconciliation
- balance snapshots
- runtime arm/disarm
- emergency kill switch
- live confirmation token

### Persistence

SQLite stores:

- runs
- trades
- experiments
- active strategy versions
- paper account state
- execution-control state
- execution orders
- exchange snapshots
- research reports

Restarting the API or scheduler does not erase the local account or strategy state.

## 4. Repository structure

```text
The-Trader/
├── app/
│   ├── agent.py          # top-level orchestration
│   ├── analytics.py      # performance metrics
│   ├── backtest.py       # historical execution engine
│   ├── broker.py         # paper accounting + simulated fills
│   ├── cli.py            # command-line interface
│   ├── config.py         # runtime configuration and safety validation
│   ├── dashboard.html    # browser research/operator console
│   ├── data.py           # validated Binance public market data
│   ├── execution.py      # sandbox/live exchange gateway
│   ├── goals.py          # objective scoring and promotion criteria
│   ├── main.py           # FastAPI application
│   ├── models.py         # domain dataclasses
│   ├── optimizer.py      # controlled self-improvement
│   ├── paper.py          # restart-safe paper execution
│   ├── policy.py         # protective execution policy
│   ├── research.py       # full research orchestration
│   ├── risk.py           # daily-loss / drawdown / sizing guard
│   ├── scheduler.py      # continuous runtime loop
│   ├── security.py       # API-key boundary
│   ├── storage.py        # SQLite persistence
│   ├── strategy.py       # SMA/RSI strategy
│   ├── stress.py         # transaction-cost sensitivity
│   └── walkforward.py    # out-of-sample validation
├── tests/                # regression and integration tests
├── data/                 # SQLite volume when running locally
├── .env.example          # complete configuration template
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 5. Requirements

- Python 3.12+
- Git
- Internet access for Binance public data and exchange API calls
- Docker Desktop / Docker Engine for container deployment
- A Binance API key + secret only for sandbox/live execution

For live trading, create credentials with the **minimum permissions necessary**. Do not enable withdrawal permissions.

## 6. Local setup

### Windows PowerShell

```powershell
git clone https://github.com/BharathWaj-K-R/The-Trader.git
cd The-Trader

python -m venv .venv
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

Copy-Item .env.example .env
```

### Linux / macOS

```bash
git clone https://github.com/BharathWaj-K-R/The-Trader.git
cd The-Trader

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env
```

Do **not** commit `.env`.

## 7. Start the application

### Development server

```bash
uvicorn app.main:app --reload
```

Open:

- Dashboard: `http://127.0.0.1:8000/`
- API docs: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`
- Liveness: `http://127.0.0.1:8000/health`
- Readiness: `http://127.0.0.1:8000/ready`

## 8. First run: research before execution

Keep:

```env
EXECUTION_MODE=paper
ENVIRONMENT=development
```

Run a backtest:

```bash
python -m app.cli backtest --symbol BTC/USDT --timeframe 30m --bars 700
```

Run self-improvement:

```bash
python -m app.cli improve --symbol BTC/USDT --timeframe 30m --bars 700 --cycles 10
```

Run walk-forward validation:

```bash
python -m app.cli walk-forward --symbol BTC/USDT --timeframe 30m --bars 700 --folds 4 --cycles 6
```

Run transaction-cost stress testing:

```bash
python -m app.cli stress-test --symbol BTC/USDT --timeframe 30m --bars 500
```

Run the complete research pipeline:

```bash
python -m app.cli full-research --symbol BTC/USDT --timeframe 30m --bars 800 --cycles 10 --folds 4
```

The full research gate combines candidate improvement, out-of-sample validation and execution-cost robustness before promoting a candidate strategy.

## 9. Paper execution

Keep:

```env
EXECUTION_MODE=paper
```

Run one paper tick:

```bash
python -m app.cli paper --symbol BTC/USDT --timeframe 30m --bars 300
```

Run continuous paper mode:

```bash
python -m app.cli daemon
```

The scheduler persists the account and active strategy in SQLite.

## 10. Sandbox execution

Sandbox mode is the bridge between research and production.

Configure:

```env
EXECUTION_MODE=sandbox
ENVIRONMENT=development
EXCHANGE_ID=binance
EXCHANGE_API_KEY=<sandbox-key>
EXCHANGE_SECRET=<sandbox-secret>
LIVE_TRADING_ENABLED=false
```

Never put production credentials into a sandbox configuration.

Start the API:

```bash
uvicorn app.main:app --reload
```

Check readiness:

```bash
curl http://127.0.0.1:8000/api/execution/preflight?symbol=BTC%2FUSDT
```

Get execution state:

```bash
curl http://127.0.0.1:8000/api/status
```

Arm the execution engine only after preflight succeeds:

```bash
curl -X POST http://127.0.0.1:8000/api/execution/arm \
  -H 'Content-Type: application/json' \
  -d '{"token":"sandbox-token"}'
```

For sandbox mode, the arming token can be any operator token stored separately from exchange credentials. For live mode it must exactly match `LIVE_CONFIRMATION_TOKEN`.

## 11. Live execution

Live mode is intentionally harder to enable than paper or sandbox mode.

### Step 1: complete research

Do not begin with live execution. Run:

```bash
python -m app.cli full-research --symbol BTC/USDT --timeframe 30m --bars 800 --cycles 10 --folds 4
```

Review the resulting report and inspect:

- out-of-sample returns
- drawdown
- benchmark-relative return
- number of trades
- robustness across folds
- cost-stress scenarios

### Step 2: configure live mode

Example:

```env
EXECUTION_MODE=live
ENVIRONMENT=production
API_KEY=<long-random-application-api-key>

EXCHANGE_ID=binance
EXCHANGE_API_KEY=<production-api-key>
EXCHANGE_SECRET=<production-api-secret>
EXCHANGE_PASSWORD=

LIVE_TRADING_ENABLED=true
LIVE_CONFIRMATION_TOKEN=<long-random-live-arming-token>

MAX_LIVE_ORDER_NOTIONAL=250
MAX_LIVE_ORDERS_PER_DAY=10
LIVE_RECONCILE_INTERVAL_SECONDS=60
KILL_SWITCH=false
```

`production` also requires `API_KEY`.

### Step 3: start the service

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Step 4: preflight

```bash
curl -H "X-API-Key: $API_KEY" \
  "http://127.0.0.1:8000/api/execution/preflight?symbol=BTC%2FUSDT"
```

Do not continue if preflight reports `ready=false`.

### Step 5: arm

```bash
curl -X POST http://127.0.0.1:8000/api/execution/arm \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"token":"'$LIVE_CONFIRMATION_TOKEN'"}'
```

Arming is persisted separately from strategy state.

### Step 6: execute a strategy tick

```bash
curl -X POST http://127.0.0.1:8000/api/execution/signal \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTC/USDT","timeframe":"30m"}'
```

The signal endpoint is not a raw exchange bypass. The execution gateway checks mode, kill switch, arming state, daily order count, notional cap, market availability and exchange precision before submitting an order.

### Step 7: reconcile

```bash
curl -X POST http://127.0.0.1:8000/api/execution/reconcile \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTC/USDT","timeframe":"30m"}'
```

Reconciliation updates locally stored order state and records exchange balance/open-order snapshots.

## 12. Emergency kill switch

Immediately stop new execution:

```bash
curl -X POST http://127.0.0.1:8000/api/execution/kill-switch \
  -H "X-API-Key: $API_KEY"
```

The scheduler checks the kill switch before executing a tick.

Disarm normally:

```bash
curl -X POST http://127.0.0.1:8000/api/execution/disarm \
  -H "X-API-Key: $API_KEY"
```

Reset the live kill switch only after investigating the reason it was triggered:

```bash
curl -X POST http://127.0.0.1:8000/api/execution/kill-switch/reset \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"token":"'$LIVE_CONFIRMATION_TOKEN'"}'
```

## 13. Manual order endpoint

A manual order endpoint exists for sandbox/live operations:

```text
POST /api/execution/order
```

Example body:

```json
{
  "symbol": "BTC/USDT",
  "timeframe": "30m",
  "order_type": "limit",
  "side": "buy",
  "amount": 0.001,
  "price": 50000,
  "reason": "operator_test"
}
```

The endpoint is protected by API authentication and execution gating. It does not exist as a shortcut around live limits.

## 14. Execution API

### Runtime

- `GET /health`
- `GET /ready`
- `GET /api/status`
- `GET /api/config`

### Research

- `POST /api/backtest`
- `POST /api/improve`
- `POST /api/walk-forward`
- `POST /api/research/full`
- `GET /api/experiments`
- `GET /api/runs`
- `GET /api/reports`

### Paper

- `POST /api/paper/tick`
- `POST /api/paper/reset`
- `GET /api/trades`

### Execution

- `GET /api/execution/preflight`
- `GET /api/execution/orders`
- `GET /api/execution/snapshots`
- `POST /api/execution/arm`
- `POST /api/execution/disarm`
- `POST /api/execution/kill-switch`
- `POST /api/execution/kill-switch/reset`
- `POST /api/execution/order`
- `POST /api/execution/signal`
- `POST /api/execution/reconcile`

In production all private endpoints require:

```http
X-API-Key: <API_KEY>
```

## 15. Docker deployment

Create `.env` first.

Then:

```bash
docker compose up --build
```

The default compose file starts:

```text
trader
   |
   +-- FastAPI
   +-- dashboard
   +-- Swagger
   +-- shared SQLite volume

paper-scheduler
   |
   +-- continuous runtime loop
   +-- shared SQLite volume
```

For sandbox/live execution, the scheduler automatically switches to the configured execution mode.

## 16. Production checklist

Before production:

1. Run the complete CI suite.
2. Run full research on the chosen symbol/timeframe.
3. Run walk-forward validation.
4. Review transaction-cost sensitivity.
5. Test sandbox execution.
6. Test restart persistence.
7. Verify reconciliation.
8. Verify API-key enforcement.
9. Verify the kill switch.
10. Set conservative order/notional limits.
11. Use exchange credentials with no withdrawal permissions.
12. Keep `LIVE_TRADING_ENABLED=false` until the operator is ready.
13. Arm live execution manually after preflight.

## 17. Security model

Do not commit:

- exchange API keys
- exchange secrets
- live confirmation tokens
- application API keys
- `.env`
- SQLite files containing operational secrets or sensitive state

Recommended deployment practices:

- environment variables or a secrets manager
- least-privilege exchange keys
- no withdrawal permission
- restricted network access
- HTTPS reverse proxy
- application API key in production
- separate sandbox and production credentials
- backups for the execution database
- centralized logs
- monitoring/alerting

## 18. Testing

Install development dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
pytest -q
```

GitHub Actions runs the same suite on repository changes.

The test suite covers accounting, API behavior, security boundaries, risk limits, strategy behavior, optimizer behavior, walk-forward logic, cost sensitivity, storage persistence, paper state, execution controls and research orchestration.

## 19. Important limitations

This is a production-oriented trading platform implementation, but it is **not a guarantee of profitability or operational correctness on every exchange**.

The current exchange adapter is deliberately limited to **Binance spot via CCXT**. Exchange-specific differences in precision, rate limits, market availability, order semantics, fees and outages must still be validated in the target account.

The system does not implement:

- withdrawals
- leverage
- futures/options
- cross-exchange routing
- multi-broker portfolio netting
- high-frequency execution
- guaranteed stop orders at the exchange level
- institutional-grade event streaming

Those are separate engineering domains.

## 20. Recommended rollout

```text
Stage 1: Research
    ↓
Stage 2: Paper
    ↓
Stage 3: Sandbox
    ↓
Stage 4: Tiny live exposure
    ↓
Stage 5: Reconciliation + monitoring
    ↓
Stage 6: Controlled scale-up
```

Do not skip stages because a backtest looked pretty. Markets have a talent for humiliating certainty.

## 21. License

MIT
