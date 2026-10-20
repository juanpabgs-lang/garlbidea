from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"
DATA = BACKEND / "data"
SNAPSHOT = DATA / "snapshot"
HISTORY = DATA / "history"
FIXTURES = DATA / "fixtures"
PROFILES = BACKEND / "profiles"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND / ".env", extra="ignore")

    api_host: str = "0.0.0.0"
    api_port: int = 8011
    profile: str = "garleb"
    approved_providers: str = ""
    openai_base_url: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    census_api_key: str = ""
    comtrade_api_key: str = ""
    regional_relay_url: str = ""
    user_agent: str = "GARLEB-Desk/0.1 (public-data research; +https://norfront.local)"

    def approved_set(self) -> set[str]:
        return {p.strip().lower() for p in self.approved_providers.split(",") if p.strip()}


settings = Settings()
