"""Runtime settings, read from environment variables with safe local defaults."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")  # real environment variables win over the file

# Business rules that are configuration, not code paths.
MAX_SEATS_PER_BOOKING = 10
CURRENCY = "USD"


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'bus.db'}")
    # Browser origins allowed to call this API (comma-separated). The frontend is a
    # separate app on its own origin, so the browser enforces CORS against this list.
    cors_origins: tuple[str, ...] = tuple(
        o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()
    )


def get_settings() -> Settings:
    return Settings()