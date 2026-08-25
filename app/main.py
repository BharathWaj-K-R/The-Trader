from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .agent import TradingAgent

app = FastAPI(title="The-Trader", version="2.0.0")
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


def _validate_request(request: MarketRequest) -> None:
    if "/" not in request.symbol or request.symbol.count("/") != 1:
        raise HTTPException(status_code=422, detail="symbol must look like BASE/QUOTE, e.g. BTC/USDT")
    if not request.timeframe or len(request.timeframe) > 10:
        raise HTTPException(status_code=422, detail="invalid timeframe")


@app.get("/health")
def health():
    return {"status": "ok", "mode": "paper-only", "version": app.version}


@app.get("/api/status")
def status():
    paper = agent.paper_engine()
    return {
        "mode": "paper-only",
        "paper_only": True,
        "strategy": agent.params.as_dict(),
        "paper": paper.snapshot(),
    }


@app.get("/api/trades")
def trades():
    return agent.store.recent("trades")


@app.get("/api/experiments")
def experiments():
    return agent.store.recent("experiments")


@app.get("/api/runs")
def runs():
    return agent.store.recent("runs")


@app.get("/api/reports")
def reports():
    return agent.store.recent("research_reports")


@app.get("/")
def dashboard():
    return FileResponse(Path(__file__).with_name("dashboard.html"))


@app.post("/api/backtest")
def backtest(request: BacktestRequest):
    _validate_request(request)
    try:
        result, trades, analytics = agent.backtest(request.symbol, request.timeframe, request.bars)
        return {
            "goal": result,
            "analytics": analytics,
            "trades": [trade.__dict__ for trade in trades],
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/improve")
def improve(request: ImproveRequest):
    _validate_request(request)
    try:
        result, history = agent.improve(
            request.symbol, request.timeframe, request.bars, request.cycles,
        )
        return {
            "goal": result,
            "strategy": agent.params.as_dict(),
            "experiments": history,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/walk-forward")
def walk_forward(request: WalkForwardRequest):
    _validate_request(request)
    try:
        return agent.walk_forward(
            request.symbol,
            request.timeframe,
            request.bars,
            request.folds,
            request.cycles,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/paper/tick")
def paper_tick(request: MarketRequest):
    _validate_request(request)
    try:
        return agent.paper_engine(request.symbol, request.timeframe).tick()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/paper/reset")
def paper_reset(request: MarketRequest):
    _validate_request(request)
    try:
        return agent.paper_engine(request.symbol, request.timeframe).reset()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
