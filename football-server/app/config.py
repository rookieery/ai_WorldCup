"""Application configuration loaded from environment variables via Pydantic Settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for all environment-dependent values."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./football_world_cup.db"

    # ── Redis ─────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False

    # ── Deepseek AI ───────────────────────────────────────────────────
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    # ── CORS ──────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # ── Application ───────────────────────────────────────────────────
    APP_ENV: str = "development"
    SCRAPER_ENABLED: bool = False

    # ── Scraper ───────────────────────────────────────────────────────
    FIFA_SCHEDULE_URL: str = "https://www.fifa.com/fifaplus/en/tournaments/mens/worldcup/2026/matchschedule"
    FIFA_MATCH_URL: str = "https://www.fifa.com/fifaplus/en/tournaments/mens/worldcup/2026/matchcenter"
    SCRAPER_CONCURRENCY: int = 3
    SCRAPER_TIMEOUT: int = 30
    SCRAPER_RETRY_MAX: int = 3

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


settings = Settings()
