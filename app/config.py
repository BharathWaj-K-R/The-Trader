from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    initial_capital: float = 10000.0
    max_position_fraction: float = 0.20
    max_daily_loss_fraction: float = 0.02
    max_drawdown_fraction: float = 0.10
    fee_bps: float = 10.0
    slippage_bps: float = 5.0
    stop_loss_fraction: float = 0.03
    take_profit_fraction: float = 0.06
    max_holding_bars: int = 0
    cooldown_bars: int = 0
    data_source: str = "binance"
    symbol: str = "BTC/USDT"
    timeframe: str = "30m"

    execution_mode: str = "paper"
    environment: str = "development"
    exchange_id: str = "binance"
    exchange_api_key: str | None = None
    exchange_secret: str | None = None
    exchange_password: str | None = None
    live_trading_enabled: bool = False
    live_confirmation_token: str | None = None
    max_live_order_notional: float = 250.0
    max_live_orders_per_day: int = 10
    live_reconcile_interval_seconds: int = 60
    kill_switch: bool = False

    scheduler_interval_seconds: int = 300
    database_url: str = "sqlite:///./data/agent.db"
    api_key: str | None = None

    # Grok AI research layer. Never expose this key to the browser.
    xai_api_key: str | None = None
    xai_model: str = "grok-4.6"
    ai_enabled: bool = False
    ai_timeout_seconds: float = 60.0
    ai_max_turns: int = 5

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def validate_runtime_policy(self):
        if self.initial_capital <= 0:
            raise ValueError("INITIAL_CAPITAL must be positive")
        if not 0 < self.max_position_fraction <= 1:
            raise ValueError("MAX_POSITION_FRACTION must be in (0,1]")
        if not 0 < self.max_daily_loss_fraction < 1:
            raise ValueError("MAX_DAILY_LOSS_FRACTION must be in (0,1)")
        if not 0 < self.max_drawdown_fraction < 1:
            raise ValueError("MAX_DRAWDOWN_FRACTION must be in (0,1)")
        if self.stop_loss_fraction < 0 or self.take_profit_fraction < 0:
            raise ValueError("protective exit fractions cannot be negative")
        if self.scheduler_interval_seconds < 30:
            raise ValueError("SCHEDULER_INTERVAL_SECONDS must be at least 30")
        if self.live_reconcile_interval_seconds < 15:
            raise ValueError("LIVE_RECONCILE_INTERVAL_SECONDS must be at least 15")
        if self.execution_mode.lower() not in {"paper", "sandbox", "live"}:
            raise ValueError("EXECUTION_MODE must be paper, sandbox, or live")
        if self.max_live_order_notional <= 0:
            raise ValueError("MAX_LIVE_ORDER_NOTIONAL must be positive")
        if self.max_live_orders_per_day < 1:
            raise ValueError("MAX_LIVE_ORDERS_PER_DAY must be at least 1")
        if self.execution_mode.lower() in {"sandbox", "live"}:
            if not self.exchange_api_key or not self.exchange_secret:
                raise ValueError("Exchange API credentials are required for sandbox/live mode")
        if self.execution_mode.lower() == "live":
            if not self.live_trading_enabled:
                raise ValueError("LIVE_TRADING_ENABLED must be true for live mode")
            if not self.live_confirmation_token:
                raise ValueError("LIVE_CONFIRMATION_TOKEN is required for live mode")
        if self.ai_timeout_seconds <= 0:
            raise ValueError("AI_TIMEOUT_SECONDS must be positive")
        if not 1 <= self.ai_max_turns <= 12:
            raise ValueError("AI_MAX_TURNS must be between 1 and 12")
        if self.ai_enabled and not self.xai_api_key:
            raise ValueError("XAI_API_KEY is required when AI_ENABLED=true")
        return self


settings = Settings()
