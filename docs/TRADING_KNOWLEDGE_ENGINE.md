# Trading Knowledge Engine

This document describes the deterministic trading principles now embedded in The-Trader. It is deliberately separate from any one educational video because the referenced YouTube video could not be retrieved in the current build environment. No claim is made that this module is a transcript or reproduction of that video.

## Principles implemented

### Trend quality
SMA direction alone can be noisy when the fast and slow averages are nearly equal. The strategy can require a minimum normalized gap between the fast and slow averages before accepting a signal.

### Volatility awareness
ATR as a percentage of price provides a normalized estimate of recent movement. The strategy can reject conditions that are too quiet for the strategy or abnormally volatile for the configured risk profile.

### Volume/liquidity confirmation
A current-volume-to-recent-average ratio can be used as a confirmation filter. It is a proxy for participation, not a guarantee of liquidity or future price movement.

### Risk/reward discipline
The existing execution policy retains stop-loss, take-profit, maximum holding period and cooldown controls. The default protective configuration targets a 2:1 take-profit-to-stop distance (6% / 3%), but this must still be validated against actual strategy behavior rather than assumed profitable.

### Benchmark awareness
The research engine compares strategy return with buy-and-hold benchmark return and computes excess return. A positive return is not automatically treated as an edge if a passive benchmark performed better.

### Out-of-sample validation
Candidate strategies are subjected to walk-forward validation so parameters are not accepted solely because they fit the same data used for tuning.

### Cost awareness
Candidate strategies are tested against multiple fee/slippage scenarios. Robustness must survive realistic execution friction.

### Overfitting control
The optimizer changes a bounded parameter at a time, records experiments, and the AI Strategy Lab restricts proposals to a known parameter surface. Arbitrary AI-generated trading code is not executable.

## Current implementation surface

`StrategyParams` now exposes optional deterministic filters:

- `use_trend_quality`
- `min_trend_gap_pct`
- `use_volatility_filter`
- `atr_window`
- `min_atr_pct`
- `max_atr_pct`
- `use_volume_confirmation`
- `volume_window`
- `min_volume_ratio`

The default values keep legacy strategy behavior permissive. The AI Strategy Lab can test these filters as bounded hypotheses. A filter is not considered useful until backtest, walk-forward, and cost-stress evidence supports it.

## AI interaction

Grok can:

1. inspect the deterministic evidence;
2. identify weaknesses;
3. propose one bounded change;
4. evaluate the deterministic result;
5. act as an adversarial critic.

Grok cannot place orders, change exchange credentials, bypass the risk engine, disable the kill switch, or execute arbitrary generated code.

## Practical interpretation

The engine is designed to answer:

> Does this strategy exhibit a repeatable, risk-adjusted edge after benchmark comparison and execution costs?

It is not designed to promise profits. Markets are non-stationary and model or strategy performance can deteriorate.
