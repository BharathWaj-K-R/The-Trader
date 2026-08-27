# The-Trader Web

Customer-facing React + TypeScript product UI for The-Trader.

## Design direction

The frontend follows a calm, monochrome shadcn/ui system: deep neutral surfaces, warm white text, white primary actions, restrained borders, tight typography, and very limited semantic color for financial meaning. Avoid generic SaaS gradients, neon crypto styling, excessive cards, heavy shadows, and decorative noise.

The navigation is decision-first:

- Overview
- Research
- Portfolio
- Execution
- Activity
- Risk & Safety
- Settings

Local UI primitives live under `src/components/ui`, with shared product composition in `src/components/` and domain pages under `src/pages/`.

## Local development

Start the backend first from the repository root:

```powershell
python -m uvicorn app.main:app --reload
```

Then from `web/`:

```powershell
npm install
npm run dev
```

Open the Vite URL printed by the server, normally `http://localhost:5173`.

The Vite development server proxies `/api`, `/health`, and `/ready` to the local FastAPI service so the browser can use a single origin.

## Production build

```powershell
npm run build
```

The build runs TypeScript compilation followed by Vite production bundling.

## Product areas

- Overview: portfolio, market context, system posture, recent activity
- Research: backtest, controlled improvement, validation and experiment history
- Portfolio: balances, position accounting and persisted trades
- Execution: preflight, arm/disarm, kill switch and reconciliation
- Activity: research and execution timeline
- Risk & Safety: risk budget and runtime safety state
- Settings: workspace defaults and client API access

## API access

When configured, the browser sends the application access key as `X-API-Key`. The frontend keeps that client key in `sessionStorage` for the current browser session. Exchange credentials are never entered into the customer UI and remain server-side.

## Architecture

`src/App.tsx` owns route selection and shared server refresh/actions. Feature screens are split into `src/pages/`. Shared customer-facing building blocks are under `src/components/`, and reusable shadcn-style primitives remain under `src/components/ui/`. API requests and TypeScript domain models live under `src/lib/`.

Keep the frontend modular. Do not return to a large monolithic page component, do not fabricate market data, and do not expose exchange secrets in browser state.
