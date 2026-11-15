from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS

app = FastAPI(title="EPIC Bus Booking API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "Idempotency-Key"],
)


@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok"}