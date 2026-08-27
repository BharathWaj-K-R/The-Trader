# AGENTS.md — The-Trader Engineering Diary

This file is the persistent engineering diary for agents working on The-Trader. It records architectural truth, important decisions, verified work, failures, and unresolved blockers.

## Operating contract

Follow the Ultimate Autonomous Software Engineering Protocol supplied with the project: audit before changing behavior; trace UI → state → API → backend → persistence → response → UI; implement complete slices; test and regress; perform security/reliability/UX/performance reviews; perform creative improvement; and finish with a zero-loose-ends review.

Never fabricate test results, runtime verification, market data, exchange behavior, or deployment status.

## Product direction

The-Trader is a trading research and execution platform. The frontend is a customer-facing product, not a demo dashboard.

Frontend visual direction: monochrome shadcn/ui, calm and easy on the eyes, light neutral surfaces, restrained borders, strong typography, compact but readable financial information, minimal decorative color, and semantic financial color only when it communicates real gain/loss or risk meaning.

Do not introduce generic SaaS gradients, neon crypto styling, excessive cards, excessive shadows, decorative animation, or fake metrics.

## Runtime modes

- paper: local simulated execution
- sandbox: exchange/test environment where supported
- live: real spot execution behind explicit credentials, preflight, arming, risk limits, and kill switch

No derivatives, leverage, withdrawals, or unsafe execution shortcuts should be added casually.

## Current architecture

Backend: Python + FastAPI + Pydantic + CCXT + SQLite.
Frontend: React + TypeScript + Vite + Tailwind CSS + local shadcn-style primitives + Recharts + Lucide.
Infrastructure: Docker, Docker Compose, GitHub Actions.

Important backend domains include market data, strategy, backtesting, optimization, walk-forward validation, cost stress, risk, paper trading, execution, reconciliation, persistence, scheduling, and the Grok AI research layer.

## Frontend architecture rule

Keep application code modular. Domain pages belong under page/feature modules and shared UI primitives under components/ui. Avoid large monolithic JSX modules.

## AI architecture rule

Grok is a research scientist, not an unrestricted execution authority. The AI may analyze real persisted data, propose bounded parameter changes, critique candidates, classify market regimes, identify anomalies, generate audit-friendly trade journals, and inspect current product state through read-only tools.

It must never receive exchange credentials and must never bypass deterministic risk or execution gates.

The current AI evolution cycle is:

```text
baseline strategy
  -> Grok analysis
  -> bounded parameter proposal
  -> deterministic backtest
  -> walk-forward validation
  -> transaction-cost stress
  -> adversarial Grok critic
  -> deterministic + critic promotion gate
  -> strategy activation only if both gates pass
```

The active parameter surface is deliberately bounded to the deterministic strategy. There is no arbitrary AI-generated executable trading code.

The AI layer uses the xAI Responses API with strict JSON-schema outputs and a bounded read-only function-call loop. Server-side configuration is required and the browser never receives `XAI_API_KEY`.

## Trading knowledge architecture

The deterministic strategy now has optional, testable market-context filters:

- trend quality using normalized fast/slow SMA separation;
- volatility regime using ATR as a percentage of price;
- volume participation confirmation using current/recent volume ratio;
- existing protective stop-loss, take-profit, holding-period and cooldown policy;
- benchmark-relative evaluation;
- walk-forward out-of-sample validation;
- transaction-cost stress testing.

Default filter parameters remain permissive so existing behavior is not silently changed. The optimizer and AI Strategy Lab can evaluate these filters as hypotheses.

The referenced YouTube video `qJap-CZoV6g` could not be retrieved in the available web environment and its transcript/metadata was not found by search. The repository therefore must not claim to reproduce the video's exact teachings. The implemented knowledge layer is a general evidence-driven trading framework compatible with the existing architecture.

## Verification diary

### 2026-08-27 — Initial repository pass
- Repository inspected through GitHub integration.
- GitHub repository is writable by the connected account.
- Frontend had a real build failure caused by an over-compressed monolithic `web/src/App.tsx` with parser errors.
- Backend CI was verified passing in an available GitHub Actions run; an older frontend job failed before the refactor.
- User environment successfully installed frontend dependencies with `npm install`; local Vite reproduced the App.tsx parser error.
- A monochrome theme was applied and then inverted to a light monochrome palette at the token level.

### 2026-08-27 — Modular frontend pass
- Added persistent `AGENTS.md` diary to the repository.
- Extracted application shell into `web/src/components/app-shell.tsx`.
- Added reusable page primitives in `web/src/components/page-primitives.tsx`.
- Added modular pages for Overview, Research, Portfolio, Execution, Activity, Risk, and Settings.
- Replaced the previous monolithic `web/src/App.tsx` with route-aware composition and centralized refresh/action handling.
- Preserved the existing API client and real backend data paths rather than introducing fake data.
- Updated the app shell to avoid the implicit React namespace in TypeScript.
- Moved client API-key persistence from localStorage to sessionStorage.
- Added `web/README.md` describing frontend architecture and local development.

### 2026-08-27 — Runtime/API fixes
- Fixed the frontend black-screen runtime failure caused by nested `status?.strategy.*` access.
- Added a React error boundary so future runtime failures are visible instead of producing a blank root.
- Added a Vite `/api` development proxy to FastAPI at `127.0.0.1:8000`.
- Preserved the existing `GET /api/execution/preflight` contract after catching a regression during the AI pass.

### 2026-08-27 — Grok AI Strategy Lab
- Added `app/ai/` with a direct xAI Responses API client using the existing `httpx` dependency.
- Configured `AI_ENABLED`, `XAI_API_KEY`, `XAI_MODEL`, `AI_TIMEOUT_SECONDS`, and bounded `AI_MAX_TURNS` server-side.
- Added structured Pydantic schemas for strategy analysis, proposals, adversarial critique, regime assessment, anomaly assessment, and trade journaling.
- Added read-only AI tool contracts and a bounded multi-turn Responses API tool loop.
- Added `StrategyLab` evolution orchestration: analyze → propose → backtest → walk-forward → cost stress → critique → promote/reject.
- Added persisted `ai_insights` storage and `/api/ai/insights` retrieval.
- Added AI endpoints for strategy lab, copilot, analysis, regime, anomaly, and trade journal.
- Added a dedicated monochrome `AI Strategy Lab` frontend route with real API integration and a read-only Research Copilot.
- Corrected the xAI structured-output request shape to the current Responses API `response_format.json_schema` contract.
- Added unit coverage for AI schemas and the requirement that critic approval is additional to deterministic promotion gates.
- Added `docs/AI_STRATEGY_LAB.md` and `docs/TRADING_KNOWLEDGE_ENGINE.md`.

### 2026-08-27 — Trading knowledge implementation
- Added optional trend-quality, ATR-volatility, and volume-confirmation filters to `StrategyParams` and `MomentumStrategy`.
- Extended the scientific optimizer to mutate the bounded market-context parameters.
- Added strategy regression tests for indicator warm-up and each new filter.
- Updated AI proposals so Grok can tune or toggle only the known deterministic filters.
- Kept live execution outside AI tool authority.

### 2026-08-27 — Documentation/release pass
- Updated `.env.example` with all AI settings.
- Updated the README with AI Strategy Lab, trading-knowledge, Windows `py` setup, API routes, and release guidance.
- Added the repository diary entry recording the exact YouTube retrieval limitation rather than inventing video content.

### 2026-08-27 — CI repair and final verification
- CI run `33066492437` exposed four backend test failures after the market-context expansion; frontend passed.
- Fixed the AI proposal test fixtures, hardened AI market-context timestamp handling, and corrected strategy filter fixtures to pass indicator warm-up.
- CI run `33066630547` completed successfully. Backend `pytest -q` passed and frontend `npm run build` passed.
- The latest verified repository state is the `main` branch commit `d7b965925ab5825f03334270e05d12c569fbc5da`.

## Current release status

- Backend tests: verified passing in CI run `33066630547`.
- Frontend production build: verified passing in CI run `33066630547`.
- Grok integration: implemented, but real API execution requires the operator's own valid `XAI_API_KEY`; no external credential is present in the repository.
- Exact YouTube-video knowledge: external retrieval blocker remains. Do not claim an exact video-derived implementation without a transcript or accessible source.
- Live trading: not certified for production deployment merely because CI passes. Exchange/account behavior still requires sandbox and controlled live validation.

## Remaining achievable work

1. Add browser/E2E coverage for AI Strategy Lab, the Vite `/api` proxy, and execution controls.
2. Add stronger multi-user authentication/authorization before enterprise SaaS claims.
3. Improve realtime/event streaming and notifications for production operations.
4. Replace prompt-based execution arming with a dedicated shadcn/ui confirmation dialog.
5. Add deeper strategy modules only through deterministic, testable interfaces and validate them through the same research gates.
6. Consider AI-assisted scheduled research only after the base workflow is stable and observable.
7. Continue appending verified discoveries and fixes here.

## Release rule

Do not declare production readiness unless the relevant code path has been verified. If an external dependency prevents verification, document it as a blocker rather than masking it.
