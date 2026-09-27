from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from .agent import TradingAgent
from .analytics import summarize_equity
from .backtest import run_backtest
from .config import settings
from .notifications import NotificationGate
from .security import require_api_key
from .strategy import MomentumStrategy
from .v4 import notification_status, product_manifest, safety_manifest

app = FastAPI(title="THE TRADER", version="4.0.0")


@app.exception_handler(404)
async def not_found(request, exc):
    page = Path(__file__).with_name("404.html")
    return HTMLResponse(page.read_text(encoding="utf-8"), status_code=404)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
agent = TradingAgent()


class MarketRequest(BaseModel):
    symbol: str = "SPY"
    timeframe: str = "1h"


class BacktestRequest(MarketRequest):
    bars: int = Field(default=600, ge=200, le=1200)


class ImproveRequest(BacktestRequest):
    cycles: int = Field(default=5, ge=1, le=10)


class WalkForwardRequest(BacktestRequest):
    folds: int = Field(default=4, ge=2, le=8)
    cycles: int = Field(default=4, ge=1, le=8)


class FullResearchRequest(BacktestRequest):
    cycles: int = Field(default=6, ge=3, le=10)
    folds: int = Field(default=4, ge=2, le=8)


class AIResearchRequest(MarketRequest):
    bars: int = Field(default=500, ge=200, le=1000)


class AICopilotRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)


class AIJournalRequest(BaseModel):
    trade: dict
    market: dict


class OutcomeRequest(BaseModel):
    correct: bool
    realized_return: float
    human_action: str = "not_recorded"
    notes: str = ""


def _validate_request(request: MarketRequest) -> None:
    try:
        request.symbol, request.timeframe = request.symbol.strip().upper(), request.timeframe.strip()
        from .v4 import validate_universe
        validate_universe(request.symbol, request.timeframe)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _ai_service():
    from .ai.client import LocalAIError, LocalAIClient
    from .ai.service import StrategyLab
    client = LocalAIClient()
    if not client.enabled:
        raise HTTPException(status_code=503, detail="Local AI is disabled; enable Ollama-backed local AI in runtime configuration")
    return StrategyLab(client), LocalAIError


@app.get("/favicon.svg", include_in_schema=False)
def favicon():
    return FileResponse(Path(__file__).with_name("favicon.svg"), media_type="image/svg+xml")


@app.get("/health")
def health():
    return {"status": "ok", "mode": "paper", "version": app.version, "specification": "v4.0"}


@app.get("/ready")
def ready():
    try:
        agent.store.recent("runs", 1)
        return {"status": "ready", "database": "ok", "mode": "paper", "version": app.version}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"readiness check failed: {exc}") from exc


@app.get("/api/v4/manifest", dependencies=[Depends(require_api_key)])
def manifest():
    return product_manifest()


@app.get("/api/v4/safety", dependencies=[Depends(require_api_key)])
def safety():
    return safety_manifest()


@app.get("/api/status", dependencies=[Depends(require_api_key)])
def status():
    paper = agent.paper_engine()
    return {
        "mode": "paper",
        "environment": settings.environment,
        "paper_only": True,
        "specification": "v4.0",
        "strategy": agent.params.as_dict(),
        "paper": paper.snapshot(),
        "execution": agent.execution_status(),
        "ai": {"enabled": bool(settings.ai_enabled), "model": settings.ollama_model},
    }


@app.get("/api/config", dependencies=[Depends(require_api_key)])
def config():
    return {
        "specification": "v4.0",
        "environment": settings.environment,
        "execution_mode": "paper",
        "data_source": settings.data_source,
        "universe": ["SPY", "QQQ"],
        "timeframe": "1h",
        "initial_capital": settings.initial_capital,
        "fee_bps": settings.fee_bps,
        "slippage_bps": settings.slippage_bps,
        "stop_loss_fraction": settings.stop_loss_fraction,
        "take_profit_fraction": settings.take_profit_fraction,
        "max_position_fraction": settings.max_position_fraction,
        "max_daily_loss_fraction": settings.max_daily_loss_fraction,
        "max_drawdown_fraction": settings.max_drawdown_fraction,
        "notification_min_oos_accuracy": settings.notification_min_oos_accuracy,
        "notification_min_expectancy": settings.notification_min_expectancy,
        "notification_min_sample": settings.notification_min_sample,
        "notification_daily_limit": settings.notification_daily_limit,
        "notification_cooldown_minutes": settings.notification_cooldown_minutes,
        "ai_enabled": bool(settings.ai_enabled and settings.ai_enabled),
        "live_trading": False,
        "live_trading_enabled": False,
    }


@app.get("/api/market", dependencies=[Depends(require_api_key)])
def market(symbol: str = "SPY", timeframe: str = "1h", bars: int = 120):
    request = MarketRequest(symbol=symbol, timeframe=timeframe)
    _validate_request(request)
    if bars < 60 or bars > 1200:
        raise HTTPException(status_code=422, detail="bars must be between 60 and 1200")
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


@app.get("/api/notifications", dependencies=[Depends(require_api_key)])
def notifications():
    return agent.store.recent_notifications()


@app.get("/api/notifications/status", dependencies=[Depends(require_api_key)])
def notifications_status(symbol: str = "SPY"):
    symbol = symbol.strip().upper()
    if symbol not in {"SPY", "QQQ"}:
        raise HTTPException(status_code=422, detail="symbol must be SPY or QQQ")
    return notification_status(agent.store, symbol)


@app.post("/api/notifications/evaluate", dependencies=[Depends(require_api_key)])
def evaluate_notification(request: MarketRequest):
    _validate_request(request)
    bars = agent.market.fetch(request.symbol, request.timeframe, 200)
    signal = MomentumStrategy(agent.params).signal(bars)
    paper = agent.paper_engine(request.symbol, request.timeframe)
    equity = paper.broker.equity
    cash = paper.broker.cash
    risk = paper.risk.check(equity, cash, bars[-1].close, max(0.05, min(0.20, signal.confidence)), bars[-1].timestamp)
    gate = NotificationGate(
        agent.store,
        policy=None,
    )
    decision = gate.evaluate(
        symbol=request.symbol,
        strategy_action=signal.action,
        ai_action=None,
        risk_approved=risk.allowed,
        signal_timestamp=bars[-1].timestamp.isoformat(),
    )
    decision["risk_reason"] = risk.reason
    decision["signal_reason"] = signal.reason
    return gate.create(decision)


@app.post("/api/notifications/{notification_id}/outcome", dependencies=[Depends(require_api_key)])
def notification_outcome(notification_id: int, request: OutcomeRequest):
    try:
        agent.store.add_notification_outcome(
            notification_id,
            request.correct,
            request.realized_return,
            request.human_action,
            request.notes,
        )
        return {"status": "recorded", "notification_id": notification_id}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


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
        result = service.evolve(request.symbol, request.timeframe, bars, agent.params, agent.store.recent("experiments", 12))
        agent.store.add_ai_insight("strategy_lab", request.symbol, request.timeframe, settings.ollama_model, result)
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


@app.post("/api/ai/copilot", dependencies=[Depends(require_api_key)])
def ai_copilot(request: AICopilotRequest):
    service, error_type = _ai_service()
    try:
        answer, usage = service.copilot(request.prompt, agent)
        payload = {"answer": answer, "usage": usage, "model": settings.ollama_model}
        agent.store.add_ai_insight("copilot", settings.symbol, settings.timeframe, settings.ollama_model, payload)
        return payload
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
        goal, trades, equity = run_backtest(bars, agent.params)
        analytics = summarize_equity(equity, trades, [b.close for b in bars])
        value, usage = service.analyze(request.symbol, request.timeframe, bars, agent.params, {"goal": goal, "analytics": analytics}, agent.store.recent("experiments", 12))
        payload = {"analysis": value.model_dump(), "usage": usage}
        agent.store.add_ai_insight("strategy_analysis", request.symbol, request.timeframe, settings.ollama_model, payload)
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
        goal, _, _ = run_backtest(bars, agent.params)
        value, usage = service.regime(request.symbol, request.timeframe, bars, goal)
        payload = {"regime": value.model_dump(), "usage": usage}
        agent.store.add_ai_insight("regime", request.symbol, request.timeframe, settings.ollama_model, payload)
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
        agent.store.add_ai_insight("anomaly", request.symbol, request.timeframe, settings.ollama_model, payload)
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
        agent.store.add_ai_insight("trade_journal", str(request.trade.get("symbol", settings.symbol)), settings.timeframe, settings.ollama_model, payload)
        return payload
    except error_type as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
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


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(Path(__file__).with_name("dashboard.html"))
