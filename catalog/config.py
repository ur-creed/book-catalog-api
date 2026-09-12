from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Runtime settings. Override with CATALOG_ env vars (e.g. CATALOG_PORT=9000)."""

    model_config = SettingsConfigDict(env_prefix="CATALOG_", extra="ignore")

    seed_path: Path = ROOT / "data" / "books.json"
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True


settings = Settings()
