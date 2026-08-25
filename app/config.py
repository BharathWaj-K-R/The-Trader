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
    paper_only: bool = True
    environment: str = "development"
    api_key: str | None = None
    scheduler_interval_seconds: int = 300
    database_url: str = "sqlite:///./data/agent.db"
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
        if self.environment.lower() == "production" and not self.api_key:
            raise ValueError("API_KEY is required in production")
        if not self.paper_only:
            raise ValueError("This build is paper-only")
        return self


settings = Settings()
