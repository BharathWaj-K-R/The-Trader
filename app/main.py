from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .agent import TradingAgent
from .config import settings
from .security import require_api_key

app = FastAPI(title="The-Trader", version="3.1.0")
agent = TradingAgent()


class MarketRequest(BaseModel):
    symbol: str = "BTC/USDT"
    timeframe: str = "30m"


class BacktestRequest(MarketRequest):
    bars: int = Field(default=300, ge=60, le=2000)


class ImproveRequest(BacktestRequest):
    cycles: int = Field(default=5, ge=1, le=50)


class WalkForwardRequest(BacktestRequest):
    folds: int = Field(default=4, ge=2, le=8)
    cycles: int = Field(default=6, ge=1, le=30)


class FullResearchRequest(BacktestRequest):
    cycles: int = Field(default=10, ge=3, le=30)
    folds: int = Field(default=4, ge=2, le=8)


class AIResearchRequest(MarketRequest):
    bars: int = Field(default=400, ge=160, le=800)


class AIJournalRequest(BaseModel):
    trade: dict
    market: dict


class ExecutionArmRequest(BaseModel):
    token: str = ""


class LiveOrderRequest(MarketRequest):
    order_type: str = "market"
    side: str
    amount: float = Field(gt=0)
    price: float | None = Field(default=None, gt=0)
    reason: str = "manual"


def _validate_request(request: MarketRequest) -> None:
    request.symbol = request.symbol.strip().upper()
    request.timeframe = request.timeframe.strip()
    if "/" not in request.symbol or request.symbol.count("/") != 1:
        raise HTTPException(status_code=422, detail="symbol must look like BASE/QUOTE, e.g. BTC/USDT")
    if not request.timeframe or len(request.timeframe) > 10:
        raise HTTPException(status_code=422, detail="invalid timeframe")


def _ai_service():
    from .ai.client import GrokError, GrokClient
    from .ai.service import StrategyLab
    client = GrokClient()
    if not client.enabled:
        raise HTTPException(status_code=503, detail="Grok AI is disabled; set AI_ENABLED=true and XAI_API_KEY")
    return StrategyLab(client), GrokError


@app.get("/health")
def health():
    return {"status": "ok", "mode": settings.execution_mode, "version": app.version, "ai_enabled": bool(settings.ai_enabled and settings.xai_api_key)}


@app.get("/ready")
def ready():
    try:
        agent.store.recent("runs", 1)
        return {"status": "ready", "database": "ok", "mode": settings.execution_mode, "version": app.version}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"readiness check failed: {exc}") from exc


@app.get("/api/status", dependencies=[Depends(require_api_key)])
def status():
    paper = agent.paper_engine()
    return {"mode": settings.execution_mode, "environment": settings.environment, "paper_only": settings.execution_mode == "paper", "strategy": agent.params.as_dict(), "paper": paper.snapshot(), "execution": agent.execution_status(), "ai": {"enabled": bool(settings.ai_enabled and settings.xai_api_key), "model": settings.xai_model}}


@app.get("/api/config", dependencies=[Depends(require_api_key)])
def config():
    return {"environment": settings.environment, "execution_mode": settings.execution_mode, "exchange_id": settings.exchange_id, "live_trading_enabled": settings.live_trading_enabled, "symbol": settings.symbol, "timeframe": settings.timeframe, "initial_capital": settings.initial_capital, "max_position_fraction": settings.max_position_fraction, "max_daily_loss_fraction": settings.max_daily_loss_fraction, "max_drawdown_fraction": settings.max_drawdown_fraction, "fee_bps": settings.fee_bps, "slippage_bps": settings.slippage_bps, "stop_loss_fraction": settings.stop_loss_fraction, "take_profit_fraction": settings.take_profit_fraction, "max_holding_bars": settings.max_holding_bars, "cooldown_bars": settings.cooldown_bars, "max_live_order_notional": settings.max_live_order_notional, "max_live_orders_per_day": settings.max_live_orders_per_day, "live_reconcile_interval_seconds": settings.live_reconcile_interval_seconds, "ai_enabled": bool(settings.ai_enabled and settings.xai_api_key), "ai_model": settings.xai_model}


@app.get("/api/market", dependencies=[Depends(require_api_key)])
def market(symbol: str = "BTC/USDT", timeframe: str = "30m", bars: int = 120):
    request = MarketRequest(symbol=symbol, timeframe=timeframe)
    _validate_request(request)
    if bars < 20 or bars > 500:
        raise HTTPException(status_code=422, detail="bars must be between 20 and 500")
    try:
        rows = agent.market.fetch(request.symbol, request.timeframe, bars)
        return [{"time": bar.timestamp.isoformat(), "open": bar.open, "high": bar.high, "low": bar.low, "close": bar.close, "volume": bar.volume} for bar in rows]
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/trades", dependencies=[Depends(require_api_key)])
def trades():
    return agent.store.recent("trades")


@app.get("/api/experiments", dependencies=[Depends(require_api_key)])
def experiments():
    return agent.store.recent("experiments")


@app.get("/api/runs", dependencies=[Depends(require_api_key)])
def runs():
    return agent.store.recent("runs")


@app.get("/api/reports", dependencies=[Depends(require_api_key)])
def reports():
    return agent.store.recent("research_reports")


@app.get("/api/ai/insights", dependencies=[Depends(require_api_key)])
def ai_insights():
    return agent.store.recent_ai_insights()


@app.get("/api/execution/orders", dependencies=[Depends(require_api_key)])
def execution_orders():
    return agent.store.recent_execution_orders(agent.execution.account_id)


@app.get("/api/execution/snapshots", dependencies=[Depends(require_api_key)])
def execution_snapshots():
    return agent.store.recent_execution_snapshots(agent.execution.account_id)


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(Path(__file__).with_name("dashboard.html"))


@app.post("/api/backtest", dependencies=[Depends(require_api_key)])
def backtest(request: BacktestRequest):
    _validate_request(request)
    try:
        result, trades, analytics = agent.backtest(request.symbol, request.timeframe, request.bars)
        return {"goal": result, "analytics": analytics, "trades": [trade.__dict__ for trade in trades]}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/improve", dependencies=[Depends(require_api_key)])
def improve(request: ImproveRequest):
    _validate_request(request)
    try:
        result, history = agent.improve(request.symbol, request.timeframe, request.bars, request.cycles)
        return {"goal": result, "strategy": agent.params.as_dict(), "experiments": history}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/walk-forward", dependencies=[Depends(require_api_key)])
def walk_forward(request: WalkForwardRequest):
    _validate_request(request)
    try:
        return agent.walk_forward(request.symbol, request.timeframe, request.bars, request.folds, request.cycles)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/research/full", dependencies=[Depends(require_api_key)])
def full_research(request: FullResearchRequest):
    _validate_request(request)
    try:
        return agent.full_research(request.symbol, request.timeframe, request.bars, request.cycles, request.folds)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/ai/strategy-lab", dependencies=[Depends(require_api_key)])
def ai_strategy_lab(request: AIResearchRequest):
    _validate_request(request)
    service, error_type = _ai_service()
    try:
        bars = agent.market.fetch(request.symbol, request.timeframe, request.bars)
        recent = agent.store.recent("experiments", 12)
        result = service.evolve(request.symbol, request.timeframe, bars, agent.params, recent)
        agent.store.add_ai_insight("strategy_lab", request.symbol, request.timeframe, settings.xai_model, result)
        if result["promotion"]["promoted"]:
            from .models import StrategyParams
            candidate = StrategyParams(**result["candidate"]["params"])
            agent.params = candidate
            agent.store.activate_strategy(candidate.as_dict(), result["candidate"]["goal"]["score"])
        return result
    except error_type as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/ai/analyze", dependencies=[Depends(require_api_key)])
def ai_analyze(request: AIResearchRequest):
    _validate_request(request)
    service, error_type = _ai_service()
    try:
        bars = agent.market.fetch(request.symbol, request.timeframe, request.bars)
        from .backtest import run_backtest
        from .analytics import summarize_equity
        goal, trades, equity = run_backtest(bars, agent.params)
        analytics = summarize_equity(equity, trades, [b.close for b in bars])
        value, usage = service.analyze(request.symbol, request.timeframe, bars, agent.params, {"goal": goal, "analytics": analytics}, agent.store.recent("experiments", 12))
        payload = {"analysis": value.model_dump(), "usage": usage}
        agent.store.add_ai_insight("strategy_analysis", request.symbol, request.timeframe, settings.xai_model, payload)
        return payload
    except error_type as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/ai/regime", dependencies=[Depends(require_api_key)])
def ai_regime(request: AIResearchRequest):
    _validate_request(request)
    service, error_type = _ai_service()
    try:
        bars = agent.market.fetch(request.symbol, request.timeframe, request.bars)
        from .backtest import run_backtest
        goal, _, _ = run_backtest(bars, agent.params)
        value, usage = service.regime(request.symbol, request.timeframe, bars, goal)
        payload = {"regime": value.model_dump(), "usage": usage}
        agent.store.add_ai_insight("regime", request.symbol, request.timeframe, settings.xai_model, payload)
        return payload
    except error_type as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/ai/anomaly", dependencies=[Depends(require_api_key)])
def ai_anomaly(request: AIResearchRequest):
    _validate_request(request)
    service, error_type = _ai_service()
    try:
        bars = agent.market.fetch(request.symbol, request.timeframe, request.bars)
        value, usage = service.anomaly(request.symbol, request.timeframe, bars, agent.store.recent("trades", 25), agent.execution_status())
        payload = {"anomaly": value.model_dump(), "usage": usage}
        agent.store.add_ai_insight("anomaly", request.symbol, request.timeframe, settings.xai_model, payload)
        return payload
    except error_type as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/ai/journal", dependencies=[Depends(require_api_key)])
def ai_journal(request: AIJournalRequest):
    service, error_type = _ai_service()
    try:
        value, usage = service.journal(request.trade, agent.params.as_dict(), request.market)
        payload = {"journal": value.model_dump(), "usage": usage}
        agent.store.add_ai_insight("trade_journal", str(request.trade.get("symbol", settings.symbol)), settings.timeframe, settings.xai_model, payload)
        return payload
    except error_type as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/execution/preflight", dependencies=[Depends(require_api_key)])
def execution_preflight(symbol: str = "BTC/USDT"):
    return agent.execution_preflight(symbol.strip().upper())


@app.post("/api/execution/arm", dependencies=[Depends(require_api_key)])
def execution_arm(request: ExecutionArmRequest):
    try:
        return agent.arm_execution(request.token)
    except Exception as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@app.post("/api/execution/disarm", dependencies=[Depends(require_api_key)])
def execution_disarm():
    try:
        return agent.disarm_execution()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/execution/kill-switch", dependencies=[Depends(require_api_key)])
def execution_kill_switch():
    return agent.activate_kill_switch()


@app.post("/api/execution/kill-switch/reset", dependencies=[Depends(require_api_key)])
def execution_kill_switch_reset(request: ExecutionArmRequest):
    try:
        return agent.reset_kill_switch(request.token)
    except Exception as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@app.post("/api/execution/order", dependencies=[Depends(require_api_key)])
def execution_order(request: LiveOrderRequest):
    _validate_request(request)
    try:
        if settings.execution_mode == "paper":
            raise HTTPException(status_code=409, detail="Manual exchange orders are disabled in paper mode")
        return agent.execution.place_order(request.symbol, request.order_type, request.side.lower(), request.amount, request.price, request.reason)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/execution/signal", dependencies=[Depends(require_api_key)])
def execution_signal(request: MarketRequest):
    _validate_request(request)
    try:
        return agent.execute_signal(request.symbol, request.timeframe)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/execution/reconcile", dependencies=[Depends(require_api_key)])
def execution_reconcile(request: MarketRequest):
    _validate_request(request)
    try:
        return agent.reconcile_execution(request.symbol)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/paper/tick", dependencies=[Depends(require_api_key)])
def paper_tick(request: MarketRequest):
    _validate_request(request)
    try:
        return agent.paper_engine(request.symbol, request.timeframe).tick()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/paper/reset", dependencies=[Depends(require_api_key)])
def paper_reset(request: MarketRequest):
    _validate_request(request)
    try:
        return agent.paper_engine(request.symbol, request.timeframe).reset()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
