import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

# Business rules configuration.
MAX_SEATS_PER_BOOKING = 10
CURRENCY = "USD"


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'bus.db'}")
    auto_seed: bool = os.getenv("AUTO_SEED", "1") != "0"
    cors_origins: tuple[str, ...] = tuple(
        o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()
    )


def get_settings() -> Settings:
    return Settings()