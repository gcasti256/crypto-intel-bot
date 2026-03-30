from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    discord_token: str = ""
    discord_client_id: str = ""

    groq_api_key: str = ""

    database_url: str = "sqlite+aiosqlite:///data/crypto_intel.db"

    redis_url: str = ""

    coingecko_base_url: str = "https://api.coingecko.com/api/v3"

    log_level: str = "INFO"

    alert_check_interval_seconds: int = 60
    news_refresh_interval_seconds: int = 300


def get_settings() -> Settings:
    return Settings()
