import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.config import settings
from app.modules.marketdata.api import router as marketdata_router
from app.modules.portfolio.api import router as portfolio_router
from app.modules.strategy.api import router as strategy_router
from app.modules.reporting.api import router as reporting_router
from app.main import app


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
                "/api/v1/marketdata",
                "/api/v1/portfolio", 
                "/api/v1/strategies",
                "/api/v1"
            ]
            
            # Проверяем что есть хотя бы один путь с каждым префиксом
            for prefix in expected_prefixes:
                found = any(path.startswith(prefix) for path in paths.keys())
                assert found, f"No routes found with prefix {prefix}"

    def test_health_endpoint(self):
        """Тест health endpoint"""
        test_app = create_test_app()
        with TestClient(test_app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert "version" in data
            assert "environment" in data

    def test_root_endpoint(self):
        """Тест root endpoint"""
        test_app = create_test_app()
        with TestClient(test_app) as client:
            response = client.get("/")
            assert response.status_code == 200
            
            data = response.json()
            assert "message" in data
            assert "version" in data
            assert "environment" in data
            assert "debug" in data


class TestRealApplication:
    """Тесты для реального приложения"""

    @patch('app.main.scheduler')
    def test_real_app_initialization(self, mock_scheduler):
        """Тест инициализации реального приложения"""
        from app.main import app
        
        # Проверяем что приложение создано
        assert app is not None
        assert app.title == settings.app_name
        assert app.version == settings.version

    @patch('app.main.setup_scheduler')
    @patch('app.main.scheduler')
    def test_real_app_endpoints_exist(self, mock_scheduler, mock_setup):
        """Тест что endpoints существуют в реальном приложении"""
        mock_scheduler.running = False
        with TestClient(app) as client:
            # Тестируем основные endpoints
            response = client.get("/")
            assert response.status_code == 200
            
            response = client.get("/health")  
            assert response.status_code == 200

    @patch('app.main.setup_scheduler')
    @patch('app.main.scheduler')
    def test_config_endpoint_non_production(self, mock_scheduler, mock_setup):
        """Тест config endpoint в не-продакшен среде"""
        mock_scheduler.running = False
        with patch.object(settings, 'environment', 'development'):
            with TestClient(app) as client:
                response = client.get("/config")
                assert response.status_code == 200
                
                data = response.json()
                assert "app_name" in data
                assert "version" in data
                assert "database" in data
                assert "moex" in data

    @patch('app.main.setup_scheduler')
    @patch('app.main.scheduler')
    def test_config_endpoint_production(self, mock_scheduler, mock_setup):
        """Тест config endpoint в продакшен среде"""
        mock_scheduler.running = False
        with patch.object(settings, 'environment', 'production'):
            with TestClient(app) as client:
                response = client.get("/config")
                assert response.status_code == 200
                
                data = response.json()
                assert data == {"message": "Config endpoint disabled in production"}

    def test_cors_middleware_added(self):
        """Тест что CORS middleware добавлен"""
        # Проверяем что middleware в списке
        middleware_classes = []
        for middleware in app.user_middleware:
            if hasattr(middleware, 'cls'):
                middleware_classes.append(middleware.cls)
            else:
                # Для старых версий FastAPI
                middleware_classes.append(middleware[0])
                
        from starlette.middleware.cors import CORSMiddleware
        assert CORSMiddleware in middleware_classes

    def test_routers_included(self):
        """Тест что все роутеры подключены"""
        # Получаем все роуты
        routes = app.routes
        route_paths = [route.path for route in routes if hasattr(route, 'path')]
        
        # Проверяем что есть роуты с нужными префиксами
        expected_prefixes = [
            f"{settings.api_prefix}/marketdata",
            f"{settings.api_prefix}/portfolio", 
            f"{settings.api_prefix}/strategies",
            settings.api_prefix
        ]
        
        for prefix in expected_prefixes:
            found = any(path.startswith(prefix) for path in route_paths)
            assert found, f"No routes found with prefix {prefix}"
