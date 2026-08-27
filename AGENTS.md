# AGENTS.md — The-Trader Engineering Diary

This file is the persistent engineering diary for agents working on The-Trader. It is not a generic prompt dump. It records the repository's current architectural truth, important decisions, verified work, failures, and unresolved blockers.

## Operating contract

Follow the project's Ultimate Autonomous Software Engineering Protocol: audit before changing behavior; trace UI → state → API → backend → persistence → response → UI; implement complete slices; test and regress; perform security/reliability/UX/performance reviews; perform a creative product-improvement pass; and finish with a zero-loose-ends review.

Never fabricate test results, runtime verification, market data, exchange behavior, or deployment status.

## Product direction

The-Trader is a trading research and execution platform. The frontend is a customer-facing product, not a demo dashboard.

Frontend visual direction: monochrome shadcn/ui, calm and easy on the eyes, deep neutral surfaces, restrained borders, excellent typography, compact but readable financial information, minimal decorative color, and semantic financial color only when it communicates real gain/loss or risk meaning.

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

Keep application code modular. Do not recreate a giant App.tsx. Domain pages belong under feature/page modules and shared UI primitives belong under components/ui. Server state must be treated as server state; avoid unnecessary duplicated global state.

## Verification diary

### 2026-08-27
- Repository inspected through GitHub integration.
- GitHub repository is writable by the connected account.
- The frontend had a real build failure caused by an over-compressed monolithic `web/src/App.tsx` with parser errors.
- Backend CI was verified passing in the available GitHub Actions run; the frontend job in that older run failed before the current refactor.
- A monochrome theme was applied previously, but current work is treating the theme and component architecture as one coherent product system.
- Local user environment successfully installs frontend dependencies with `npm install`; local Vite exposed an App.tsx parser error.
- User requested this diary to be maintained continuously.

## Current work queue

1. Replace monolithic frontend with modular customer UX.
2. Preserve real API integration and eliminate dead controls.
3. Keep the UI monochrome and shadcn-based.
4. Add strong loading/error/empty states.
5. Verify backend tests and frontend build through CI.
6. Update README whenever setup/architecture changes.
7. Append meaningful discoveries/fixes to this diary.

## Release rule

Do not declare production readiness unless the relevant code path has been verified. If an external dependency prevents verification, document it as a blocker rather than masking it.
