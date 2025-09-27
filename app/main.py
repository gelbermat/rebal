from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.scheduler import setup_scheduler
from app.logging_config import get_logger
from app.modules.marketdata.api import router as marketdata_router
from app.modules.portfolio.api import router as portfolio_router
from app.modules.strategy.api import router as strategy_router
from app.modules.reporting.api import router as reporting_router


scheduler = AsyncIOScheduler()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        f"Starting {settings.app_name} v{settings.version} in {settings.environment} environment"
    )

    if settings.scheduler.enabled:
        logger.info("Starting scheduler...")
        setup_scheduler(scheduler)
        scheduler.start()
        logger.info("Scheduler started successfully")

    yield

    if scheduler.running:
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()
        logger.info("Scheduler shutdown complete")


app = FastAPI(
    title=settings.app_name,
    description="Low-activity investment service for MOEX",
    version=settings.version,
    debug=settings.debug,
    docs_url=settings.docs_url if not settings.environment == "production" else None,
    redoc_url=settings.redoc_url if not settings.environment == "production" else None,
    lifespan=lifespan,
)

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

app.include_router(
    marketdata_router, prefix=f"{settings.api_prefix}/marketdata", tags=["MarketData"]
)
app.include_router(
    portfolio_router, prefix=f"{settings.api_prefix}/portfolio", tags=["Portfolio"]
)
app.include_router(
    strategy_router, prefix=f"{settings.api_prefix}/strategies", tags=["Strategy"]
)
app.include_router(reporting_router, prefix=settings.api_prefix, tags=["Reporting"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": f"{settings.app_name} service is running",
        "version": settings.version,
        "environment": settings.environment,
        "debug": settings.debug,
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.version,
        "environment": settings.environment,
    }


@app.get("/config")
async def get_config():
    """Получение текущей конфигурации (без секретных данных)"""
    if settings.environment == "production":
        return {"message": "Config endpoint disabled in production"}

    return {
        "app_name": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "debug": settings.debug,
        "api_prefix": settings.api_prefix,
        "database": {
            "echo": settings.database.echo,
            "pool_size": settings.database.pool_size,
            "max_overflow": settings.database.max_overflow,
        },
        "moex": {
            "api_url": settings.moex.api_url,
            "timeout": settings.moex.timeout,
            "rate_limit": settings.moex.rate_limit,
            "retries": settings.moex.retries,
        },
        "scheduler": {
            "enabled": settings.scheduler.enabled,
            "timezone": settings.scheduler.timezone,
            "market_data_sync_cron": settings.scheduler.market_data_sync_cron,
            "rebalancing_cron": settings.scheduler.rebalancing_cron,
        },
        "logging": {
            "level": settings.logging.level,
            "file_path": settings.logging.file_path,
        },
        "reporting": {
            "max_report_history": settings.reporting.max_report_history,
            "default_date_range_days": settings.reporting.default_date_range_days,
            "cache_reports": settings.reporting.cache_reports,
            "cache_ttl_minutes": settings.reporting.cache_ttl_minutes,
        },
    }
