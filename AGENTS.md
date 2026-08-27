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

Important backend domains include market data, strategy, backtesting, optimization, walk-forward validation, cost stress, risk, paper trading, execution, reconciliation, persistence, and scheduling.

## Frontend architecture rule

Keep application code modular. Domain pages belong under page/feature modules and shared UI primitives under components/ui. Avoid large monolithic JSX modules.

## Verification diary

### 2026-08-27 — Initial repository pass
- Repository inspected through GitHub integration.
- GitHub repository is writable by the connected account.
- Frontend had a real build failure caused by an over-compressed monolithic `web/src/App.tsx` with parser errors.
- Backend CI was verified passing in an available GitHub Actions run; an older frontend job failed before the refactor.
- User environment successfully installed frontend dependencies with `npm install`; local Vite reproduced the App.tsx parser error.
- A monochrome theme was applied and then tightened at the token/component level.

### 2026-08-27 — Modular frontend pass
- Added this persistent `AGENTS.md` diary to the repository.
- Extracted application shell into `web/src/components/app-shell.tsx`.
- Added reusable page primitives in `web/src/components/page-primitives.tsx`.
- Added modular pages for Overview, Research, Portfolio, Execution, Activity, Risk, and Settings.
- Replaced the previous monolithic `web/src/App.tsx` with route-aware composition and centralized refresh/action handling.
- Preserved the existing API client and real backend data paths rather than introducing fake data.
- Current execution UI intentionally uses existing backend controls and does not invent unsupported manual-order functionality.
- Updated the app shell to avoid the implicit React namespace in TypeScript.

## Current verification state

- Backend test job has previously passed in CI.
- The earlier frontend CI failure was a parser/build failure in the old App.tsx; the current modular tree requires a fresh CI run to prove the new build is green.
- The repository's GitHub workflow is the source of truth for current CI status.
- Local market/exchange verification requires the user's runtime environment and network access; do not claim it from repository inspection alone.

## Current work queue

1. Confirm the new frontend production build in CI.
2. Add/verify stronger shadcn/ui primitives as needed (Tabs, Dialog, Table, Toast/Sonner, Form) without introducing a second UI library.
3. Add proper frontend tests and critical E2E journeys.
4. Upgrade research visualization and experiment drill-down using real report data.
5. Replace prompt-based arming with a proper shadcn/ui dialog when the execution UX is ready.
6. Review API typing and server-state caching; add TanStack Query only if it materially improves the current workflow.
7. Update README whenever setup/architecture changes.
8. Continue appending verified discoveries and fixes here.

## Release rule

Do not declare production readiness unless the relevant code path has been verified. If an external dependency prevents verification, document it as a blocker rather than masking it.
