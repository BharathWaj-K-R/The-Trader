# AI Strategy Lab

The-Trader's AI layer uses Grok as a research scientist, not as an unrestricted trading authority.

## Safety model

```text
Market data
  -> deterministic strategy
  -> baseline backtest
  -> Grok analysis
  -> bounded parameter proposal
  -> deterministic backtest
  -> walk-forward validation
  -> transaction-cost stress
  -> Grok adversarial critic
  -> promotion gate
  -> optional strategy activation
```

Grok never receives exchange credentials and the AI endpoints never place orders. Existing execution controls remain the only path to sandbox/live exchange actions.

## Configuration

Set these server-side in `.env`:

```env
AI_ENABLED=true
XAI_API_KEY=your-xai-api-key
XAI_MODEL=grok-4.6
AI_TIMEOUT_SECONDS=60
```

Keep the key out of the browser and out of Git. The current xAI Responses API is available at `https://api.x.ai/v1`, and `grok-4.6` supports structured outputs and tool calling. See the official xAI documentation for current model/tool availability. 

## Strategy evolution

`POST /api/ai/strategy-lab` runs one controlled evolution cycle. It:

1. evaluates the active deterministic strategy;
2. asks Grok to diagnose strengths, weaknesses and a market regime;
3. asks Grok for exactly one bounded parameter proposal;
4. backtests the candidate;
5. runs walk-forward validation;
6. runs fee/slippage stress scenarios;
7. asks an adversarial Grok critic to review the evidence;
8. promotes the candidate only when the deterministic gates and AI critic both approve;
9. persists the complete result in `ai_insights`;
10. activates the candidate only after the promotion gate passes.

The candidate is restricted to the current strategy parameter surface: fast SMA, slow SMA, RSI window, RSI entry and RSI exit. The AI cannot add arbitrary code or indicators.

## Other AI capabilities

- `POST /api/ai/analyze`: structured strategy analysis.
- `POST /api/ai/regime`: market-regime assessment.
- `POST /api/ai/anomaly`: operational/strategy anomaly assessment.
- `POST /api/ai/journal`: audit-friendly explanation of a completed trade.
- `GET /api/ai/insights`: persisted AI insight history.

## Frontend

The React console exposes **AI Strategy Lab** in the Workspace navigation. The page shows the AI diagnosis, proposed parameter change, baseline/candidate metrics, walk-forward evidence, cost-stress evidence, adversarial critic verdict, and promotion result.

## Why the AI is constrained

An LLM is probabilistic. Strategy performance and risk decisions need reproducible rules. The AI therefore proposes and critiques; deterministic research and execution policies remain the judges and gatekeepers.
