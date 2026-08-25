# The-Trader Web

Customer-facing React + TypeScript product UI for The-Trader.

## Design direction

The UI deliberately avoids generic monochrome SaaS styling. It uses a quiet graphite surface, warm-white typography, one restrained indigo action color, and semantic green/red only where financial state requires it.

The layout is built around a persistent navigation rail and decision-first screens:

- Overview
- Research
- Portfolio
- Execution
- Activity
- Risk & Safety
- Settings

The application uses local shadcn/ui-style components under `src/components/ui`, with Lucide icons and Recharts for the market pulse visualization.

## Local development

From `web/`:

```bash
npm install
npm run dev
```

The Vite development server proxies `/api`, `/health`, and `/ready` to `http://127.0.0.1:8000`.

Run the backend separately:

```bash
cd ..
uvicorn app.main:app --reload
```

Then open the Vite URL printed by the dev server.

## Production container

The `web/Dockerfile` builds the Vite application and serves the static bundle through nginx.

nginx proxies backend traffic through the same origin:

```text
/api/*   -> trader:8000/api/*
/health  -> trader:8000/health
/ready   -> trader:8000/ready
```

This avoids browser-side CORS configuration for the customer application.

## Product principles

- No fake market numbers in the interface.
- Loading, empty and error states are explicit.
- Live execution is visually separated from research.
- Risk and kill-switch state stays visible.
- The UI consumes the real FastAPI APIs and persisted research/execution data.
