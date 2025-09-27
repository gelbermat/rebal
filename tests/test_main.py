import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.config import settings
from app.modules.marketdata.api import router as marketdata_router
from app.modules.portfolio.api import router as portfolio_router
from app.modules.strategy.api import router as strategy_router
from app.modules.reporting.api import router as reporting_router


@asynccontextmanager
async def app_lifespan_for_tests(app: FastAPI):
    """Lifespan для тестов без планировщика"""
    yield


def create_test_app() -> FastAPI:
    """Создание тестового приложения без планировщика"""
    test_app = FastAPI(
        title=settings.app_name,
        description="Test version of Low-activity investment service for MOEX",
        version=settings.version,
        debug=settings.debug,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        lifespan=app_lifespan_for_tests,
    )

    # Добавляем маршруты
    test_app.include_router(
        marketdata_router,
        prefix=f"{settings.api_prefix}/marketdata",
        tags=["MarketData"],
    )
    test_app.include_router(
        portfolio_router, prefix=f"{settings.api_prefix}/portfolio", tags=["Portfolio"]
    )
    test_app.include_router(
        strategy_router, prefix=f"{settings.api_prefix}/strategies", tags=["Strategy"]
    )
    test_app.include_router(
        reporting_router, prefix=settings.api_prefix, tags=["Reporting"]
    )

    # Добавляем базовые endpoints
    @test_app.get("/")
    async def root():
        """Health check endpoint"""
        return {
            "message": f"{settings.app_name} service is running",
            "version": settings.version,
            "environment": settings.environment,
            "debug": settings.debug,
        }

    @test_app.get("/health")
    async def health():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "version": settings.version,
            "environment": settings.environment,
        }

    return test_app


@pytest.mark.integration
class TestMainApplication:

    def test_app_startup(self):
        test_app = create_test_app()
        with TestClient(test_app) as client:
            response = client.get("/docs")
            assert response.status_code == 200

    def test_health_check(self):
        test_app = create_test_app()
        with TestClient(test_app) as client:
            response = client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "version" in data

    @pytest.mark.api
    def test_api_routes_registered(self):
        test_app = create_test_app()
        with TestClient(test_app) as client:
            response = client.get("/openapi.json")
            assert response.status_code == 200

            schema = response.json()
            assert "paths" in schema

            paths = schema["paths"]
            expected_prefixes = [
                "/marketdata",
                "/portfolio",
                "/strategy",
                "/orders",
                "/reporting",
            ]
