from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .agent import TradingAgent
from .config import settings
from .security import require_api_key

app = FastAPI(title="The-Trader", version="2.3.0")
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


class StressRequest(BacktestRequest):
    pass


def _validate_request(request: MarketRequest) -> None:
    request.symbol = request.symbol.strip().upper()
    request.timeframe = request.timeframe.strip()
    if "/" not in request.symbol or request.symbol.count("/") != 1:
        raise HTTPException(status_code=422, detail="symbol must look like BASE/QUOTE, e.g. BTC/USDT")
    if not request.timeframe or len(request.timeframe) > 10:
        raise HTTPException(status_code=422, detail="invalid timeframe")


@app.get("/health")
def health():
    return {"status": "ok", "mode": "paper-only", "version": app.version}


@app.get("/ready")
def ready():
    try:
        agent.store.recent("runs", 1)
        return {"status": "ready", "database": "ok", "mode": "paper-only", "version": app.version}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"readiness check failed: {exc}") from exc


@app.get("/api/status", dependencies=[Depends(require_api_key)])
def status():
    paper = agent.paper_engine()
    return {"mode": "paper-only", "paper_only": True, "environment": settings.environment,
            "strategy": agent.params.as_dict(), "paper": paper.snapshot()}


@app.get("/api/config", dependencies=[Depends(require_api_key)])
def config():
    return {"environment": settings.environment, "paper_only": settings.paper_only,
            "symbol": settings.symbol, "timeframe": settings.timeframe,
            "initial_capital": settings.initial_capital,
            "max_position_fraction": settings.max_position_fraction,
            "max_daily_loss_fraction": settings.max_daily_loss_fraction,
            "max_drawdown_fraction": settings.max_drawdown_fraction,
            "fee_bps": settings.fee_bps, "slippage_bps": settings.slippage_bps,
            "stop_loss_fraction": settings.stop_loss_fraction,
            "take_profit_fraction": settings.take_profit_fraction,
            "max_holding_bars": settings.max_holding_bars,
            "cooldown_bars": settings.cooldown_bars}


@app.get("/api/trades", dependencies=[Depends(require_api_key)])
def trades(): return agent.store.recent("trades")


@app.get("/api/experiments", dependencies=[Depends(require_api_key)])
def experiments(): return agent.store.recent("experiments")


@app.get("/api/runs", dependencies=[Depends(require_api_key)])
def runs(): return agent.store.recent("runs")


@app.get("/api/reports", dependencies=[Depends(require_api_key)])
def reports(): return agent.store.recent("research_reports")


@app.get("/", include_in_schema=False)
def dashboard(): return FileResponse(Path(__file__).with_name("dashboard.html"))


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


@app.post("/api/stress-test", dependencies=[Depends(require_api_key)])
def stress_test(request: StressRequest):
    _validate_request(request)
    try:
        return agent.stress_test(request.symbol, request.timeframe, request.bars)
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
