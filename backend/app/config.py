"""Settings, read from environment variables (backend/.env in development)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")  # real environment variables win over the file

# Browser origins allowed to call this API. The frontend is a separate app on its
# own origin, so the browser enforces CORS against this list.
CORS_ORIGINS = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()
]