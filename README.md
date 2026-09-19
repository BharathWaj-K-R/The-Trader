# The-Trader

**The-Trader is a full-scale algorithmic trading platform and research engine with paper, sandbox, and live-capable spot execution modes.**

It combines validated market data, deterministic strategy logic, research/backtesting, controlled self-improvement, walk-forward validation, transaction-cost stress testing, persistent accounting, risk controls, exchange execution, reconciliation, operator controls, a web console, CLI, Docker deployment, CI, and an AI research layer powered by Grok when explicitly enabled.

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
                  DASHBOARD / API / AI LAB
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

### Trading knowledge engine

The deterministic strategy can optionally use explicit, testable market-quality filters:

- trend-quality filter based on fast/slow SMA separation
- normalized ATR volatility filter
- volume participation confirmation
- configurable filter thresholds
- bounded optimizer mutations for the new parameters

These filters are evidence-driven configuration, not guaranteed edge. The complete design is documented in `docs/TRADING_KNOWLEDGE_ENGINE.md`.

### Grok AI Strategy Lab

When `AI_ENABLED=true`, the server-side AI layer can:

- analyze the active strategy and research evidence
- classify the current market regime
- propose one bounded strategy change per evolution cycle
- run deterministic backtests against the proposal
- run walk-forward validation
- run transaction-cost stress tests
- perform adversarial candidate review
- persist AI research insights
- produce audit-friendly trade journals
- inspect current strategy, research, trades, market context, and risk through read-only tools

The AI is a research scientist, not an execution authority. It cannot place, cancel, arm, reset, or modify exchange orders through its tools, and it cannot bypass deterministic risk or promotion gates.

The evolution path is:

```text
Active strategy
    ↓
Grok analysis
    ↓
One bounded proposal
    ↓
Deterministic backtest
    ↓
Walk-forward validation
    ↓
Cost stress
    ↓
Grok adversarial critic
    ↓
Deterministic + critic promotion gate
    ↓
Promote or reject
```

The AI layer uses xAI's Responses API with structured JSON Schema outputs and a bounded read-only tool loop. See `docs/AI_STRATEGY_LAB.md`.

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
- AI insights

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
│   ├── dashboard.html    # legacy browser console
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
│   ├── strategy.py       # SMA/RSI + optional market-quality filters
│   ├── stress.py         # transaction-cost sensitivity
│   ├── walkforward.py    # out-of-sample validation
│   └── ai/               # Grok research and Strategy Lab
├── web/
│   ├── src/components/   # application shell + reusable UI
│   ├── src/pages/        # domain pages including AI Strategy Lab
│   ├── src/lib/          # API client + types
│   └── vite.config.ts    # /api development proxy
├── tests/                # regression and integration tests
├── docs/
│   ├── AI_STRATEGY_LAB.md
│   └── TRADING_KNOWLEDGE_ENGINE.md
├── data/                 # SQLite volume when running locally
├── .env.example          # complete configuration template
├── AGENTS.md             # persistent agent engineering diary
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 5. Requirements

- Python 3.12+
- Git
- Node.js / npm for the web console
- Internet access for Binance public data and exchange API calls
- Docker Desktop / Docker Engine for container deployment
- A Binance API key + secret only for sandbox/live execution
- An xAI API key only when Grok features are enabled

For live trading, create credentials with the **minimum permissions necessary**. Do not enable withdrawal permissions.

## 6. Local setup

### Windows PowerShell

```powershell
git clone https://github.com/BharathWaj-K-R/The-Trader.git
cd The-Trader

py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

Copy-Item .env.example .env
```

Activation is optional. On Windows, using the environment's `python.exe` directly avoids PATH and PowerShell activation problems.

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

### Backend

Windows:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Linux/macOS:

```bash
uvicorn app.main:app --reload
```

Open:

- API docs: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`
- Liveness: `http://127.0.0.1:8000/health`
- Readiness: `http://127.0.0.1:8000/ready`

### Frontend

Open another terminal:

```powershell
cd The-Trader\web
npm install
npm run dev
```

Then open:

`http://localhost:5173`

The Vite development server proxies `/api/*` to the FastAPI service on `127.0.0.1:8000`.

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

## 9. AI Strategy Lab

Configure on the **backend only**:

```env
AI_ENABLED=true
XAI_API_KEY=<your-xai-api-key>
XAI_MODEL=grok-4.6
AI_TIMEOUT_SECONDS=60
AI_MAX_TURNS=5
```

Never place `XAI_API_KEY` in React, browser storage, or source control.

Start the frontend and open:

`http://localhost:5173/ai-lab`

The Strategy Lab provides:

- **Research Copilot**: ask Grok to inspect current strategy, research history, trades, market context and risk using read-only tools.
- **Evolution Cycle**: Grok analyzes the current strategy, proposes one bounded change, then The-Trader runs deterministic backtest, walk-forward, cost stress, and AI critique.
- **Promotion Evidence**: baseline vs candidate metrics, robustness evidence, cost-stress evidence, critic verdict and final promotion decision.
- **Persisted Insight History**: results are saved in SQLite and available from `GET /api/ai/insights`.

AI endpoints:

- `POST /api/ai/copilot`
- `POST /api/ai/strategy-lab`
- `POST /api/ai/analyze`
- `POST /api/ai/regime`
- `POST /api/ai/anomaly`
- `POST /api/ai/journal`
- `GET /api/ai/insights`

The AI never bypasses execution controls. It cannot directly place exchange orders.

## 10. Trading knowledge engine

The deterministic strategy can test market-quality concepts alongside SMA/RSI:

```text
Trend alignment
    +
Volatility regime
    +
Volume confirmation
    +
Protective risk/reward policy
    +
Benchmark comparison
    +
Walk-forward validation
    +
Cost stress
```

Optional strategy parameters include:

```text
use_trend_quality
min_trend_gap_pct
use_volatility_filter
atr_window
min_atr_pct
max_atr_pct
use_volume_confirmation
volume_window
min_volume_ratio
```

These parameters can be evaluated by the deterministic optimizer and proposed by Grok within strict bounds. They are not assumed to improve profitability until the research evidence says so.

See `docs/TRADING_KNOWLEDGE_ENGINE.md` for the detailed rationale and limitations.

## 11. Paper execution

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

## 12. Sandbox execution

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

Start the API and validate preflight before arming.

## 13. Live execution

Live mode is intentionally harder to enable than paper or sandbox mode.

Complete research, walk-forward validation and transaction-cost stress testing first. Then configure production credentials, preflight, arm explicitly, execute only through the execution gateway, and reconcile regularly.

Example:

```env
EXECUTION_MODE=live
ENVIRONMENT=production
API_KEY=<long-random-application-api-key>
EXCHANGE_ID=binance
EXCHANGE_API_KEY=<production-api-key>
EXCHANGE_SECRET=<production-api-secret>
LIVE_TRADING_ENABLED=true
LIVE_CONFIRMATION_TOKEN=<long-random-live-arming-token>
MAX_LIVE_ORDER_NOTIONAL=250
MAX_LIVE_ORDERS_PER_DAY=10
LIVE_RECONCILE_INTERVAL_SECONDS=60
KILL_SWITCH=false
```

Do not continue if execution preflight is not ready.

## 14. Emergency kill switch

Immediately stop new execution through:

```text
POST /api/execution/kill-switch
```

Reset only after investigating why it was triggered.

## 15. Execution API

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

### AI

- `GET /api/ai/insights`
- `POST /api/ai/copilot`
- `POST /api/ai/strategy-lab`
- `POST /api/ai/analyze`
- `POST /api/ai/regime`
- `POST /api/ai/anomaly`
- `POST /api/ai/journal`

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

In production private endpoints require:

```http
X-API-Key: <API_KEY>
```

## 16. Docker deployment

Create `.env` first, then:

```bash
docker compose up --build
```

The default compose setup includes the FastAPI service and a continuous scheduler with shared SQLite persistence.

## 17. Production checklist

Before production:

1. Run the complete CI suite.
2. Run full research on the chosen symbol/timeframe.
3. Run walk-forward validation.
4. Review transaction-cost sensitivity.
5. Review any AI Strategy Lab promotion evidence.
6. Test sandbox execution.
7. Test restart persistence.
8. Verify reconciliation.
9. Verify API-key enforcement.
10. Verify the kill switch.
11. Set conservative order/notional limits.
12. Use exchange credentials with no withdrawal permissions.
13. Keep `LIVE_TRADING_ENABLED=false` until the operator is ready.
14. Arm live execution manually only after preflight succeeds.

## 18. Security model

Do not commit:

- exchange API keys
- exchange secrets
- live confirmation tokens
- application API keys
- xAI API keys
- `.env`
- SQLite files containing sensitive operational state

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

## 19. Testing

Install development dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
pytest -q
```

Frontend build:

```bash
cd web
npm install
npm run build
```

GitHub Actions runs the backend tests and frontend build on repository changes.

The tests cover accounting, API behavior, security boundaries, risk limits, strategy behavior including market-quality filters, optimizer behavior, walk-forward logic, cost sensitivity, storage persistence, paper state, execution controls, research orchestration, and AI promotion-gate behavior.

## 20. Important limitations

This is a production-oriented trading platform implementation, but it is **not a guarantee of profitability or operational correctness on every exchange**.

The current exchange adapter is deliberately limited to **Binance spot via CCXT**. Exchange-specific differences in precision, rate limits, market availability, order semantics, fees and outages must still be validated in the target account.

The AI layer improves research workflow and hypothesis generation; it does not prove an edge. LLM outputs can be wrong, and the product therefore constrains the AI to structured proposals and read-only context gathering.

The system does not implement:

- withdrawals
- leverage
- futures/options
- cross-exchange routing
- multi-broker portfolio netting
- high-frequency execution
- guaranteed stop orders at the exchange level
- institutional-grade event streaming
- arbitrary AI-generated trading code execution

## 21. Recommended rollout

```text
Stage 1: Research
    ↓
Stage 2: AI-assisted research
    ↓
Stage 3: Paper
    ↓
Stage 4: Sandbox
    ↓
Stage 5: Tiny live exposure
    ↓
Stage 6: Reconciliation + monitoring
    ↓
Stage 7: Controlled scale-up
```

Do not skip stages because a backtest looked pretty. Markets have a talent for humiliating certainty.

## 22. License

MIT
