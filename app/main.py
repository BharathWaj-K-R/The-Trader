from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .agent import TradingAgent
from .config import settings
from .security import require_api_key

app = FastAPI(title="The-Trader", version="3.0.0")
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


@app.get("/health")
def health():
    return {"status": "ok", "mode": settings.execution_mode, "version": app.version}


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
    return {"mode": settings.execution_mode, "environment": settings.environment, "paper_only": settings.execution_mode == "paper", "strategy": agent.params.as_dict(), "paper": paper.snapshot(), "execution": agent.execution_status()}


@app.get("/api/config", dependencies=[Depends(require_api_key)])
def config():
    return {"environment": settings.environment, "execution_mode": settings.execution_mode, "exchange_id": settings.exchange_id, "live_trading_enabled": settings.live_trading_enabled, "symbol": settings.symbol, "timeframe": settings.timeframe, "initial_capital": settings.initial_capital, "max_position_fraction": settings.max_position_fraction, "max_daily_loss_fraction": settings.max_daily_loss_fraction, "max_drawdown_fraction": settings.max_drawdown_fraction, "fee_bps": settings.fee_bps, "slippage_bps": settings.slippage_bps, "stop_loss_fraction": settings.stop_loss_fraction, "take_profit_fraction": settings.take_profit_fraction, "max_holding_bars": settings.max_holding_bars, "cooldown_bars": settings.cooldown_bars, "max_live_order_notional": settings.max_live_order_notional, "max_live_orders_per_day": settings.max_live_orders_per_day, "live_reconcile_interval_seconds": settings.live_reconcile_interval_seconds}


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
