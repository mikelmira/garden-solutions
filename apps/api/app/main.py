"""
Garden Solutions API - Main application entrypoint.

Layered Architecture per docs:
- api/main.py: App entrypoint
- api/routers/: Route definitions
- api/services/: Business logic
- api/schemas/: Pydantic models (DTOs)
- api/models/: SQLAlchemy database models
- api/core/: Config, Security, Database connection
"""
import logging
import logging.config
import time
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import get_settings

# ── Structured Logging Configuration ──────────────────────────
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "lifecycle": {
            "format": "%(asctime)s LIFECYCLE %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "lifecycle_console": {
            "class": "logging.StreamHandler",
            "formatter": "lifecycle",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "app.request": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "app.lifecycle": {"handlers": ["lifecycle_console"], "level": "INFO", "propagate": False},
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
}
logging.config.dictConfig(LOGGING_CONFIG)
from app.core.exceptions import AppException, app_exception_handler, generic_exception_handler
from app.core.database import SessionLocal
from app.routers import auth, clients, products, price_tiers, orders, manufacturing, moulding, order_items, delivery, sales_agents, delivery_teams, factory_teams, public, stores, skus, ops, analytics, shopify, shopify_webhooks

settings = get_settings()
logger = logging.getLogger("app.request")
lifecycle_logger = logging.getLogger("app.lifecycle")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Register exception handlers for standardized error responses
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# CORS middleware - origins from config (default: localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logger(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start) * 1000)
    logger.info("%s %s %s %dms", request.method, request.url.path, response.status_code, duration_ms)
    return response

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(clients.router, prefix=f"{settings.API_V1_STR}/clients", tags=["clients"])
app.include_router(products.router, prefix=f"{settings.API_V1_STR}/products", tags=["products"])
app.include_router(skus.router, prefix=f"{settings.API_V1_STR}/skus", tags=["skus"])
app.include_router(price_tiers.router, prefix=f"{settings.API_V1_STR}/price-tiers", tags=["price-tiers"])
app.include_router(orders.router, prefix=f"{settings.API_V1_STR}/orders", tags=["orders"])
app.include_router(manufacturing.router, prefix=f"{settings.API_V1_STR}/manufacturing", tags=["manufacturing"])
app.include_router(moulding.router, prefix=f"{settings.API_V1_STR}/moulding", tags=["moulding"])
app.include_router(order_items.router, prefix=f"{settings.API_V1_STR}/order-items", tags=["order-items"])
app.include_router(delivery.router, prefix=f"{settings.API_V1_STR}/delivery", tags=["delivery"])
app.include_router(sales_agents.router, prefix=f"{settings.API_V1_STR}/sales-agents", tags=["sales-agents"])
app.include_router(delivery_teams.router, prefix=f"{settings.API_V1_STR}/delivery-teams", tags=["delivery-teams"])
app.include_router(factory_teams.router, prefix=f"{settings.API_V1_STR}/factory-teams", tags=["factory-teams"])
app.include_router(stores.router, prefix=f"{settings.API_V1_STR}", tags=["stores"])
app.include_router(public.router, prefix=f"{settings.API_V1_STR}/public", tags=["public"])
app.include_router(ops.router, prefix=f"{settings.API_V1_STR}/ops", tags=["operations"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])
app.include_router(shopify.router, prefix=f"{settings.API_V1_STR}/shopify", tags=["shopify"])
app.include_router(shopify_webhooks.router, prefix=f"{settings.API_V1_STR}/webhooks/shopify", tags=["shopify-webhooks"])

static_dir = (Path(__file__).resolve().parent.parent / "uploads").resolve()
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(static_dir)), name="uploads")
# Backward compat: also serve /static from the same directory for old image_url records
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.on_event("startup")
def run_migrations():
    """Auto-run Alembic migrations on startup in production."""
    if settings.ENVIRONMENT == "production":
        try:
            from alembic.config import Config
            from alembic import command
            alembic_cfg = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))
            alembic_cfg.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URI)
            command.upgrade(alembic_cfg, "head")
            lifecycle_logger.info("Alembic migrations applied successfully")
        except Exception as e:
            lifecycle_logger.error(f"Migration failed: {e}")
            raise


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {"message": "Garden Solutions API V1", "status": "healthy"}


@app.get("/health")
def health_check():
    """Health check endpoint for load balancers."""
    return {"status": "healthy"}


@app.get(f"{settings.API_V1_STR}/health")
def api_health_check():
    """API health check with DB connectivity and system info."""
    import time as _time
    start = _time.time()
    db = SessionLocal()
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass
    finally:
        db.close()
    db_latency_ms = int((_time.time() - start) * 1000)

    status = "healthy" if db_ok else "degraded"
    return {
        "status": status,
        "environment": settings.ENVIRONMENT,
        "database": {"connected": db_ok, "latency_ms": db_latency_ms},
    }
