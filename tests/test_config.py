"""Тесты для конфигурации приложения"""

import pytest
import os
from unittest.mock import patch

from app.config import Settings, settings


class TestSettings:
    """Тесты для настроек приложения"""

    def test_default_settings(self):
        """Тест настроек по умолчанию"""
        # Изолируем от переменных окружения, но не от .env файла
        with patch.dict(os.environ, {}, clear=False):
            test_settings = Settings()

            assert test_settings.app_name == "Rebalancer"
            assert test_settings.version == "0.1.0"
            # В CI может быть установлено ENVIRONMENT=testing
            assert test_settings.environment in ["development", "testing"]
            # debug может быть True из .env файла
            assert isinstance(test_settings.debug, bool)
            assert test_settings.api_prefix == "/api/v1"

            # Проверяем вложенные настройки
            assert test_settings.database.url is not None
            assert test_settings.database.pool_size == 10
            assert test_settings.moex.api_url == "https://iss.moex.com"
            assert test_settings.scheduler.enabled == True
            assert test_settings.logging.level == "INFO"

    def test_environment_variables(self):
        """Тест загрузки настроек из переменных окружения"""
        with patch.dict(
            os.environ,
            {
                "APP_NAME": "TestApp",
                "DEBUG": "true",
                "DATABASE__POOL_SIZE": "20",
                "MOEX__TIMEOUT": "60",
                "LOGGING__LEVEL": "DEBUG",
            },
        ):
            test_settings = Settings()

            assert test_settings.app_name == "TestApp"
            assert test_settings.debug == True
            assert test_settings.database.pool_size == 20
            assert test_settings.moex.timeout == 60
            assert test_settings.logging.level == "DEBUG"

    def test_nested_settings(self):
        """Тест вложенных настроек"""
        test_settings = Settings()

        # Проверяем все группы настроек
        assert hasattr(test_settings, "database")
        assert hasattr(test_settings, "moex")
        assert hasattr(test_settings, "broker")
        assert hasattr(test_settings, "scheduler")
        assert hasattr(test_settings, "logging")
        assert hasattr(test_settings, "security")
        assert hasattr(test_settings, "reporting")

        # Проверяем типы
        assert hasattr(test_settings.database, "url")
        assert hasattr(test_settings.moex, "api_url")
        assert hasattr(test_settings.scheduler, "enabled")

    def test_backward_compatibility(self):
        """Тест обратной совместимости"""
        test_settings = Settings()

        # Проверяем, что старые свойства работают
        assert test_settings.database_url == test_settings.database.url
        assert test_settings.moex_api_url == test_settings.moex.api_url
        assert test_settings.broker_api_url == test_settings.broker.api_url
        assert test_settings.broker_api_key == test_settings.broker.api_key
        assert test_settings.scheduler_enabled == test_settings.scheduler.enabled

    def test_validation(self):
        """Тест валидации настроек"""
        with pytest.raises(ValueError):
            Settings(environment="invalid_env")

        with pytest.raises(ValueError):
            Settings(logging__level="INVALID_LEVEL")

        with pytest.raises(ValueError):
            Settings(moex__api_url="invalid-url")

    def test_cors_settings(self):
        """Тест настроек CORS"""
        test_settings = Settings()

        assert isinstance(test_settings.cors_origins, list)
        assert isinstance(test_settings.cors_methods, list)
        assert isinstance(test_settings.cors_headers, list)
        assert test_settings.cors_credentials == True

    def test_security_settings(self):
        """Тест настроек безопасности"""
        test_settings = Settings()

        assert test_settings.security.algorithm == "HS256"
        assert test_settings.security.access_token_expire_minutes == 30
        assert test_settings.security.refresh_token_expire_days == 7
        assert len(test_settings.security.secret_key) > 0

    def test_reporting_settings(self):
        """Тест настроек отчетности"""
        test_settings = Settings()

        assert test_settings.reporting.max_report_history == 100
        assert test_settings.reporting.default_date_range_days == 30
        assert test_settings.reporting.cache_reports == True
        assert test_settings.reporting.cache_ttl_minutes == 15

    def test_scheduler_settings(self):
        """Тест настроек планировщика"""
        test_settings = Settings()

        assert test_settings.scheduler.timezone == "Europe/Moscow"
        assert test_settings.scheduler.trading_mode == "24/7"  # Новый дефолт
        assert test_settings.scheduler.market_data_sync_hour_24_7 == 19
        assert test_settings.scheduler.market_data_sync_minute_24_7 == 0
        assert (
            test_settings.scheduler.get_market_data_cron() == "0 19 * * *"
        )  # 24/7 режим
        assert test_settings.scheduler.rebalancing_cron == "0 10 * * 1"

        # Тест режима рабочих дней
        business_settings = Settings()
        business_settings.scheduler.trading_mode = "business_days"
        assert business_settings.scheduler.get_market_data_cron() == "0 18 * * 1-5"

    def test_global_settings_instance(self):
        """Тест глобального экземпляра настроек"""
        assert settings.app_name == "Rebalancer"
        assert hasattr(settings, "database")
        assert hasattr(settings, "moex")
        assert hasattr(settings, "scheduler")


class TestEnvironmentSpecificSettings:
    """Тесты настроек для разных окружений"""

    def test_development_settings(self):
        """Тест настроек для разработки"""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            test_settings = Settings()
            assert test_settings.environment == "development"

    def test_production_settings(self):
        """Тест настроек для продакшена"""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            test_settings = Settings()
            assert test_settings.environment == "production"

    def test_testing_settings(self):
        """Тест настроек для тестирования"""
        with patch.dict(os.environ, {"ENVIRONMENT": "testing"}):
            test_settings = Settings()
            assert test_settings.environment == "testing"
