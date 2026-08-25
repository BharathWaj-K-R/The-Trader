from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    initial_capital: float = 10000.0
    max_position_fraction: float = 0.20
    max_daily_loss_fraction: float = 0.02
    max_drawdown_fraction: float = 0.10
    fee_bps: float = 10.0
    slippage_bps: float = 5.0
    data_source: str = "binance"
    symbol: str = "BTC/USDT"
    timeframe: str = "30m"
    paper_only: bool = True
    database_url: str = "sqlite:///./data/agent.db"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
