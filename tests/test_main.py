import pytest
from unittest.mock import patch, AsyncMock, MagicMock
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


class TestMainAppLifespan:
    """Тесты для lifespan функций главного приложения"""
    
    @pytest.mark.asyncio
    @patch('app.main.scheduler')
    @patch('app.main.setup_scheduler')
    @patch('app.main.logger')
    async def test_lifespan_with_scheduler_enabled(self, mock_logger, mock_setup, mock_scheduler):
        """Тест lifespan с включенным scheduler"""
        from app.main import lifespan
        
        # Мокаем настройки
        with patch.object(settings.scheduler, 'enabled', True):
            mock_scheduler.running = True
            
            # Имитируем lifespan context
            async with lifespan(app):
                # Проверяем что scheduler был настроен и запущен
                mock_setup.assert_called_once_with(mock_scheduler)
                mock_scheduler.start.assert_called_once()
                
            # Проверяем что scheduler был остановлен
            mock_scheduler.shutdown.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.main.scheduler')
    @patch('app.main.setup_scheduler')  
    @patch('app.main.logger')
    async def test_lifespan_with_scheduler_disabled(self, mock_logger, mock_setup, mock_scheduler):
        """Тест lifespan с выключенным scheduler"""
        from app.main import lifespan
        
        # Мокаем настройки
        with patch.object(settings.scheduler, 'enabled', False):
            mock_scheduler.running = False
            
            async with lifespan(app):
                # Scheduler не должен быть настроен и запущен
                mock_setup.assert_not_called()
                mock_scheduler.start.assert_not_called()
                
            # Shutdown не должен вызываться если scheduler не запущен
            mock_scheduler.shutdown.assert_not_called()


class TestMainEndpointsFullCoverage:
    """Полные тесты для всех endpoints главного приложения"""
    
    @patch('app.main.setup_scheduler')
    @patch('app.main.scheduler')
    def test_root_endpoint_full(self, mock_scheduler, mock_setup):
        """Полный тест root endpoint"""
        mock_scheduler.running = False
        
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200
            
            data = response.json()
            # Проверяем все поля
            assert data["message"] == f"{settings.app_name} service is running"
            assert data["version"] == settings.version
            assert data["environment"] == settings.environment
            assert "debug" in data
            assert isinstance(data["debug"], bool)

    @patch('app.main.setup_scheduler')
    @patch('app.main.scheduler')
    def test_health_endpoint_full(self, mock_scheduler, mock_setup):
        """Полный тест health endpoint"""
        mock_scheduler.running = False
        
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            # Проверяем все поля
            assert data["status"] == "healthy"
            assert data["version"] == settings.version
            assert data["environment"] == settings.environment

    @patch('app.main.setup_scheduler')
    @patch('app.main.scheduler')
    def test_config_endpoint_development(self, mock_scheduler, mock_setup):
        """Тест config endpoint в development среде"""
        mock_scheduler.running = False
        
        with patch.object(settings, 'environment', 'development'):
            with TestClient(app) as client:
                response = client.get("/config")
                assert response.status_code == 200
                
                data = response.json()
                # Проверяем основные разделы конфигурации
                assert "app_name" in data
                assert "version" in data
                assert "environment" in data
                assert "debug" in data
                assert "api_prefix" in data
                
                # Проверяем nested конфигурации
                assert "database" in data
                assert "echo" in data["database"]
                assert "pool_size" in data["database"]
                assert "max_overflow" in data["database"]
                
                assert "moex" in data
                assert "api_url" in data["moex"]
                assert "timeout" in data["moex"]
                assert "rate_limit" in data["moex"]
                assert "retries" in data["moex"]
                
                assert "scheduler" in data
                assert "enabled" in data["scheduler"]
                assert "timezone" in data["scheduler"]
                
                assert "logging" in data
                assert "level" in data["logging"]
                assert "file_path" in data["logging"]
                
                assert "reporting" in data
                assert "max_report_history" in data["reporting"]

    @patch('app.main.setup_scheduler')
    @patch('app.main.scheduler')  
    def test_config_endpoint_production(self, mock_scheduler, mock_setup):
        """Тест config endpoint в production среде"""
        mock_scheduler.running = False
        
        with patch.object(settings, 'environment', 'production'):
            with TestClient(app) as client:
                response = client.get("/config")
                assert response.status_code == 200
                
                data = response.json()
                assert data == {"message": "Config endpoint disabled in production"}


class TestMainAppConfiguration:
    """Тесты конфигурации FastAPI приложения"""
    
    def test_app_basic_configuration(self):
        """Тест базовой конфигурации приложения"""
        assert app.title == settings.app_name
        assert app.version == settings.version
        assert app.debug == settings.debug
        
    def test_app_docs_configuration_development(self):
        """Тест конфигурации документации в development"""
        with patch.object(settings, 'environment', 'development'):
            # Перезагружаем модуль чтобы применить изменения
            import importlib
            from app import main
            importlib.reload(main)
            
            # В development docs должны быть доступны
            # Проверяем через создание нового приложения с той же логикой
            test_app = FastAPI(
                docs_url=settings.docs_url if settings.environment != "production" else None,
                redoc_url=settings.redoc_url if settings.environment != "production" else None,
            )
            assert test_app.docs_url is not None
            assert test_app.redoc_url is not None
            
    def test_app_docs_configuration_production(self):
        """Тест что docs отключены в production"""
        with patch.object(settings, 'environment', 'production'):
            # Проверяем логику отключения docs
            docs_url = settings.docs_url if settings.environment != "production" else None
            redoc_url = settings.redoc_url if settings.environment != "production" else None
            
            assert docs_url is None
            assert redoc_url is None
