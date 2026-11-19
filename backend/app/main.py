import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api import public, admin
from app.config import Settings, get_settings
from app.database import make_engine, make_session_factory
from app.errors import DomainError
from app.models import Base

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("app")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    engine = make_engine(settings.database_url)
    session_factory = make_session_factory(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        Base.metadata.create_all(engine)
        if settings.auto_seed:
            from app.seed import seed_if_empty
            with session_factory() as db:
                if seed_if_empty(db):
                    log.info("database was empty: seeded demo data")
        yield
        engine.dispose()

    app = FastAPI(title="EPIC Bus Booking API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type", "Idempotency-Key"],
    )
    app.state.session_factory = session_factory
    app.state.engine = engine

    # ---- errors: one consistent shape, {"error": {"code", "message", ...}} -------------
    @app.exception_handler(DomainError)
    async def domain_error(_: Request, exc: DomainError):
        return JSONResponse(status_code=exc.status_code, content={
            "error": {"code": exc.code, "message": exc.message, **exc.extra}})

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        fields = [{"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]}
                  for e in exc.errors()]
        return JSONResponse(status_code=422, content={
            "error": {"code": "validation_error", "message": "Invalid request", "fields": fields}})

    @app.middleware("http")
    async def access_log(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        ms = (time.perf_counter() - start) * 1000
        if request.url.path.startswith("/api") or request.url.path == "/health":
            log.info("request method=%s path=%s status=%s duration_ms=%.1f",
                     request.method, request.url.path, response.status_code, ms)
        return response
    
    @app.get("/health", tags=["ops"])
    def health():
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok"}

    app.include_router(public.router)
    app.include_router(admin.router)

    return app


app = create_app()