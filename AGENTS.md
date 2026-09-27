# AGENTS.md — THE TRADER v4.0 Engineering Diary

## Operating contract

THE TRADER v4.0 is frozen. Implement against the specification, never silently modify the specification.

Audit before changing behavior. Trace UI → state → API → backend → persistence → response → UI. Test every changed slice. Never fabricate test results, runtime verification, market data, exchange behavior, or deployment status.

## Product authority

- Research laboratory, not a passive-income machine.
- Initial universe: SPY, QQQ.
- Initial timeframe: 1h.
- Long-only.
- Live trading is out of scope for v1.
- Sandbox execution is out of scope for v1.
- AI has zero execution authority.
- Deterministic risk has absolute veto power.
- Notifications are informational only.
- Human review is the final decision point.
- Failed strategies and negative research results remain stored.

## Runtime architecture

Backend: Python + FastAPI + Pydantic + SQLite.
Primary market data: yfinance.
Paper execution: deterministic simulator with an Alpaca Paper integration target.
Local AI: Ollama-compatible client, disabled by default.
Frontend: React + TypeScript + Vite + Tailwind/shadcn-style primitives.
Infrastructure: Docker, Docker Compose, GitHub Actions.

## AI architecture

Local AI may analyze persisted evidence, propose bounded parameter changes, classify regimes, identify anomalies, and generate audit-friendly journals.

AI may not:
- place orders
- cancel orders
- modify positions
- change risk
- approve its own notification
- bypass deterministic research gates
- execute human decisions
- generate arbitrary executable trading code

The intended evolution path is:
baseline → local AI analysis → one bounded proposal → deterministic backtest → walk-forward → cost stress → adversarial critique → deterministic promotion gate.

## Notification architecture

A notification can be generated only when:
- the deterministic strategy is actionable;
- deterministic risk approves;
- AI agrees when an AI decision is present;
- empirical OOS accuracy meets threshold;
- rolling expectancy is positive;
- minimum rolling sample exists;
- daily notification limit is available;
- cooldown is clear.

Notifications never become orders.

Human outcome data records acted/not acted, correctness, realized return, and notes.

## Current implementation diary

### v4 migration
- Locked execution mode to paper.
- Locked universe to SPY/QQQ.
- Locked timeframe to 1h.
- Replaced Binance/crypto market-data defaults with yfinance.
- Added v4 manifest and safety endpoints.
- Added deterministic notification gate and persisted outcomes.
- Added local Ollama client compatibility.
- Reworked the scheduler to paper-only.
- Removed exchange execution controls from the v4 API surface.
- Replaced the legacy dashboard with a v4 paper/research control plane.
- Added v4 scope and notification regression tests.

## Verification rules

Do not claim a test passed unless a test run or CI result proves it.

Do not claim paper performance is profitable merely because the backtest runs.

Do not claim notification eligibility until the empirical gates have accumulated the required sample.

Do not claim live readiness. v4.0 explicitly excludes live trading.

## Remaining work

1. Run and repair the complete CI suite after the v4 migration.
2. Add browser/E2E coverage for the v4 control plane and notification lifecycle.
3. Implement and verify the Alpaca Paper adapter against paper credentials.
4. Implement the frozen secondary validation source and its overlap/data-quality gate.
5. Add statistical validation and multiple-testing controls required by the master specification.
6. Add the complete 90-day paper-equivalence evidence workflow.
7. Add long-horizon 6–12 month stability tracking.
8. Keep all future research-policy changes versioned and explicit.

## Release rule

Production deployment does not equal research certification. A Render service may be operational while the strategy remains scientifically uncertified.
