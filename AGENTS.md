# AGENTS.md — The-Trader Engineering Diary

This file is the persistent engineering diary for agents working on The-Trader. It is not a generic prompt dump. It records architectural truth, important decisions, verified work, failures, and unresolved blockers.

## Operating contract

Follow the Ultimate Autonomous Software Engineering Protocol: audit before changing behavior; trace UI → state → API → backend → persistence → response → UI; implement complete slices; test and regress; perform security/reliability/UX/performance reviews; perform creative improvement; and finish with a zero-loose-ends review.

Never fabricate test results, runtime verification, market data, exchange behavior, or deployment status.

## Product direction

The-Trader is a trading research and execution platform. The frontend is a customer-facing product, not a demo dashboard.

Frontend visual direction: monochrome shadcn/ui, calm and easy on the eyes, deep neutral surfaces, restrained borders, strong typography, compact but readable financial information, minimal decorative color, and semantic financial color only when it communicates real gain/loss or risk meaning.

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

Grok is a research scientist, not an unrestricted execution authority. The AI may analyze real persisted data, propose bounded parameter changes, critique candidates, classify market regimes, identify anomalies, and generate audit-friendly trade journals. It must never receive exchange credentials and must never bypass deterministic risk/execution gates.

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

The active parameter surface is deliberately constrained to the existing strategy: fast SMA, slow SMA, RSI window, RSI entry, and RSI exit. No arbitrary code generation or arbitrary indicator injection is performed by the AI layer.

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
- Configured `AI_ENABLED`, `XAI_API_KEY`, `XAI_MODEL`, and `AI_TIMEOUT_SECONDS` server-side.
- Added structured Pydantic schemas for strategy analysis, proposals, adversarial critique, regime assessment, anomaly assessment, and trade journaling.
- Added read-only AI tool contracts for strategy, research history, risk state, trades, and market context.
- Added `StrategyLab` evolution orchestration: analyze → propose → backtest → walk-forward → cost stress → critique → promote/reject.
- Added persisted `ai_insights` storage and `/api/ai/insights` retrieval.
- Added AI endpoints for strategy lab, analysis, regime, anomaly, and trade journal.
- Added a dedicated monochrome `AI Strategy Lab` frontend route with real API integration and promotion evidence.
- Added unit coverage for structured AI schemas and the requirement that AI critic approval is in addition to deterministic promotion gates.
- Added `docs/AI_STRATEGY_LAB.md` describing setup, safety boundaries, endpoints, and evolution flow.

## Current work queue

1. Run and verify CI for the Grok Strategy Lab commit series.
2. Add a real multi-turn Responses API tool loop using the read-only tool contracts when it materially improves research context gathering.
3. Add proper frontend tests and critical E2E journeys for the API proxy, AI Strategy Lab, and execution controls.
4. Upgrade research visualization and experiment drill-down using real report data.
5. Replace prompt-based execution arming with a proper shadcn/ui confirmation dialog.
6. Review API typing and server-state caching; add TanStack Query only if it materially improves the current workflow.
7. Continue strengthening backend authentication/authorization for true multi-user SaaS before claiming enterprise production readiness.
8. Add notification/alert delivery for AI anomalies and research findings where appropriate.
9. Add richer strategy features only through deterministic, testable strategy modules rather than arbitrary AI code generation.
10. Update the README whenever setup/architecture changes.
11. Continue appending verified discoveries and fixes here.

## Release rule

Do not declare production readiness unless the relevant code path has been verified. If an external dependency prevents verification, document it as a blocker rather than masking it.
