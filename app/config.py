from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Frozen v4.0 research scope.
    initial_capital: float = 10000.0
    max_position_fraction: float = 0.20
    max_daily_loss_fraction: float = 0.02
    max_drawdown_fraction: float = 0.10
    fee_bps: float = 1.0
    slippage_bps: float = 2.0
    stop_loss_fraction: float = 0.03
    take_profit_fraction: float = 0.06
    max_holding_bars: int = 0
    cooldown_bars: int = 1

    data_source: str = "yfinance"
    symbol: str = "SPY"
    timeframe: str = "1h"
    universe: str = "SPY,QQQ"

    # v4.0 is paper-only. These values are deliberately not a live-execution API.
    execution_mode: str = "paper"
    environment: str = "development"
    paper_broker: str = "simulator"
    alpaca_paper_key: str | None = None
    alpaca_paper_secret: str | None = None
    alpaca_paper_base_url: str = "https://paper-api.alpaca.markets"

    scheduler_interval_seconds: int = 3600
    database_url: str = "sqlite:///./data/agent.db"
    api_key: str | None = None

    # Local AI is optional and has zero execution authority.
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b"
    ai_enabled: bool = False
    ai_timeout_seconds: float = 60.0
    ai_max_turns: int = 5

    # Human notification gates.
    notification_min_oos_accuracy: float = 0.58
    notification_min_expectancy: float = 0.0
    notification_min_sample: int = 50
    notification_daily_limit: int = 3
    notification_cooldown_minutes: int = 60

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
        if self.scheduler_interval_seconds < 60:
            raise ValueError("SCHEDULER_INTERVAL_SECONDS must be at least 60")
        if self.execution_mode.lower() != "paper":
            raise ValueError("THE TRADER v4.0 only permits paper mode")
        if self.data_source.lower() != "yfinance":
            raise ValueError("THE TRADER v4.0 primary data source is yfinance")
        if self.symbol.upper() not in {"SPY", "QQQ"}:
            raise ValueError("THE TRADER v4.0 universe is SPY,QQQ")
        if self.timeframe != "1h":
            raise ValueError("THE TRADER v4.0 timeframe is 1h")
        if self.paper_broker not in {"simulator", "alpaca_paper"}:
            raise ValueError("PAPER_BROKER must be simulator or alpaca_paper")
        if self.paper_broker == "alpaca_paper" and (not self.alpaca_paper_key or not self.alpaca_paper_secret):
            raise ValueError("Alpaca Paper credentials are required when PAPER_BROKER=alpaca_paper")
        if not 0 < self.notification_min_oos_accuracy <= 1:
            raise ValueError("NOTIFICATION_MIN_OOS_ACCURACY must be in (0,1]")
        if self.notification_min_sample < 1 or self.notification_daily_limit < 1:
            raise ValueError("notification sample and daily limit must be positive")
        if self.notification_cooldown_minutes < 0:
            raise ValueError("NOTIFICATION_COOLDOWN_MINUTES cannot be negative")
        return self


settings = Settings()
