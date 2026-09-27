# THE TRADER\n\n**Product-Level Master Report v4.0 implementation**\n\nTHE TRADER is a local-first quantitative research laboratory for deterministic strategy research, out-of-sample validation, paper trading, local-AI evaluation, and controlled human-in-the-loop notifications.\n\n## Frozen operating contract\n- Initial universe: **SPY, QQQ**\n- Initial timeframe: **1-hour**\n- Direction: **long-only**\n- Primary market data: **Yahoo Finance / yfinance**\n- Secondary validation: **planned research control; not yet implemented in v4.0 runtime**\n- Paper broker: **Alpaca Paper adapter target, deterministic simulator for local/offline tests**\n- Live trading: **out of scope for v1**\n- AI execution authority: **none**\n- Notification authority: **informational notifications only**\n- Risk authority: **deterministic risk engine with absolute veto**\n- Human authority: **final manual decision**\n- Evidence before narrative\n- Failed strategies and negative results are retained\n\nThe implementation intentionally rejects EXECUTION_MODE=sandbox and EXECUTION_MODE=live.\n\n## Local Ollama setup

THE TRADER's AI layer is local and disabled by default. It talks to Ollama at `http://127.0.0.1:11434` and has no execution tools. Qwen2.5:7b is the configured default and supports structured JSON output, which matches the AI schemas used by the application. https://ollama.com/library/qwen2.5:7b

1. Install Ollama for your operating system.
2. Pull and test the configured model:

```bash
ollama pull qwen2.5:7b
ollama run qwen2.5:7b
```

3. In a second terminal, from the repository root, create your local environment:

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
```

4. Edit `.env` and set:

```text
AI_ENABLED=true
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b
EXECUTION_MODE=paper
DATA_SOURCE=yfinance
```

5. Start the API/dashboard:

```bash
uvicorn app.main:app --reload
```

6. Open `http://127.0.0.1:8000`. Use **AI Lab → Analyze current strategy** after Ollama is running. The application calls Ollama's `/api/chat` endpoint directly. Ollama serves its local API on port 11434.

7. Optional paper scheduler, in a third terminal:

```bash
python -m app.scheduler
```

The scheduler only advances the SPY/QQQ paper engines. It never submits exchange orders.

If you set `API_KEY` in `.env`, use the dashboard operator menu to store that key in the browser for protected API requests. Do not commit the key.

## Product flow\n\nMarket data → validation → deterministic strategy → backtest → robustness/walk-forward/cost stress → statistical evidence → secondary validation (planned) → optional local AI → deterministic risk veto → paper trading → empirical notification gates → human notification → human outcome record.\n\nA notification is never an order.\n\n## Current implemented surface\n\n### Research\n- SPY/QQQ 1h market-data adapter using yfinance\n- OHLCV validation and duplicate/outlier rejection\n- deterministic SMA/RSI strategy with optional market-context filters\n- historical backtesting\n- benchmark-relative metrics\n- walk-forward validation\n- transaction-cost stress testing\n- bounded deterministic optimization\n- persisted experiments, strategy versions and research reports\n\n### Paper trading\n- restart-safe local paper account\n- deterministic risk guard\n- position sizing\n- daily-loss and drawdown vetoes\n- protective exits\n- persisted trades and account state\n- paper-only scheduler\n\n### Local AI\n- Ollama-compatible local model client\n- structured outputs\n- bounded read-only tool loop\n- strategy analysis / bounded proposal / adversarial critique\n- AI results cannot place, modify, cancel or approve orders\n- AI is not a promotion authority\n\n### Human-in-the-loop notifications\nThe notification gate requires all of the following:\n- actionable deterministic strategy signal\n- deterministic risk approval\n- AI agreement when an AI decision is present\n- empirical OOS accuracy at or above the configured threshold\n- positive rolling expectancy\n- minimum rolling sample size\n- daily notification limit not exceeded\n- cooldown clear\n\nHuman outcome records support:\n- correct / incorrect\n- realized return\n- acted / not acted / not recorded\n- notes\n\n## Runtime\n\n1. Copy .env.example to .env.\n2. Install requirements.txt.\n3. Start uvicorn app.main:app.\n\nThe browser console is served from /. API documentation is available at /docs.\n\nFor local AI, run Ollama separately and set AI_ENABLED=true. No cloud AI credential is required.\n\n## Safety\n\nTHE TRADER v4.0 has no live execution path in its runtime policy. Existing pre-v4 execution modules are not part of the v4 control plane and are not reachable through the v4 API.\n\nNever interpret backtest or paper results as a guarantee of future profitability.\n\n## Verification\n\nRun pytest -q.\n\nThe repository contains the existing regression suite plus new v4 scope and notification-gate tests.\n\n## Deployment\n\nRender Python service:\n- Build: pip install -r requirements.txt\n- Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT\n\nUse paper mode only. Keep AI disabled on the public service unless Ollama is separately available inside the deployment environment.\n\n## Status terminology\n- **IMPLEMENTED** means the code path exists.\n- **VERIFIED** means a test or runtime check has actually executed successfully.\n- **BLOCKED** means an external dependency prevents verification.\n- **NOT YET CERTIFIED** means the evidence gates have not accumulated enough data.\n\nTHE TRADER is a research laboratory. Its successful outcome may be evidence of a durable edge or evidence that no durable edge was found.