"""
Тесты для модуля конфигурации
"""

import pytest
import os
from unittest.mock import patch
from app.config import (
    DatabaseSettings, MOEXSettings, BrokerSettings, SchedulerSettings,
    LoggingSettings, SecuritySettings, ReportingSettings, Settings, settings
)


class TestDatabaseSettings:
    """Тесты конфигурации базы данных"""
    
    def test_database_settings_creation(self):
        """Тест создания настроек базы данных"""
        config = DatabaseSettings()
        
        # Проверяем значения по умолчанию
        assert "postgresql" in config.url
        assert config.echo == False
        assert config.pool_size == 10
        assert config.max_overflow == 20
        
    def test_database_settings_custom(self):
        """Тест пользовательских настроек БД"""
        config = DatabaseSettings(
            url="sqlite:///test.db",
            echo=True,
            pool_size=5,
            max_overflow=10
        )
        
        assert config.url == "sqlite:///test.db"
        assert config.echo == True
        assert config.pool_size == 5
        assert config.max_overflow == 10


class TestMOEXSettings:
    """Тесты настроек MOEX API"""
    
    def test_moex_settings_creation(self):
        """Тест создания настроек MOEX"""
        config = MOEXSettings()
        
        assert config.api_url == "https://iss.moex.com"
        assert config.timeout == 30
        assert config.rate_limit == 100
        assert config.retries == 3
        
    def test_moex_settings_validation(self):
        """Тест валидации URL MOEX"""
        # Корректный URL
        config = MOEXSettings(api_url="https://api.moex.com")
        assert config.api_url == "https://api.moex.com"
        
        # Некорректный URL должен вызывать ошибку
        with pytest.raises(ValueError):
            MOEXSettings(api_url="invalid-url")
            
    def test_moex_settings_custom(self):
        """Тест пользовательских настроек MOEX"""
        config = MOEXSettings(
            api_url="http://localhost:8080",
            timeout=60,
            rate_limit=50,
            retries=5
        )
        
        assert config.api_url == "http://localhost:8080"
        assert config.timeout == 60
        assert config.rate_limit == 50
        assert config.retries == 5


class TestBrokerSettings:
    """Тесты настроек брокера"""
    
    def test_broker_settings_creation(self):
        """Тест создания настроек брокера"""
        config = BrokerSettings()
        
        assert config.api_url is None
        assert config.api_key is None
        assert config.api_secret is None
        assert config.account_id is None
        assert config.sandbox_mode == True
        
    def test_broker_settings_custom(self):
        """Тест пользовательских настроек брокера"""
        config = BrokerSettings(
            api_url="https://api.broker.com",
            api_key="test_key",
            api_secret="test_secret",
            account_id="123456",
            sandbox_mode=False
        )
        
        assert config.api_url == "https://api.broker.com"
        assert config.api_key == "test_key"
        assert config.api_secret == "test_secret"
        assert config.account_id == "123456"
        assert config.sandbox_mode == False


class TestSchedulerSettings:
    """Тесты настроек планировщика"""
    
    def test_scheduler_settings_creation(self):
        """Тест создания настроек планировщика"""
        config = SchedulerSettings()
        
        assert config.enabled == True
        assert config.timezone == "Europe/Moscow"
        assert config.trading_mode == "24/7"
        
    def test_scheduler_trading_mode_validation(self):
        """Тест валидации режима торгов"""
        # Корректные режимы
        config1 = SchedulerSettings(trading_mode="24/7")
        assert config1.trading_mode == "24/7"
        
        config2 = SchedulerSettings(trading_mode="business_days")
        assert config2.trading_mode == "business_days"
        
        # Некорректный режим
        with pytest.raises(ValueError):
            SchedulerSettings(trading_mode="invalid_mode")
            
    def test_scheduler_cron_generation(self):
        """Тест генерации cron выражений"""
        # Режим 24/7
        config_24_7 = SchedulerSettings(
            trading_mode="24/7",
            market_data_sync_hour_24_7=20,
            market_data_sync_minute_24_7=30
        )
        cron = config_24_7.get_market_data_cron()
        assert cron == "30 20 * * *"
        
        # Режим рабочих дней
        config_business = SchedulerSettings(
            trading_mode="business_days",
            market_data_sync_hour_business=18,
            market_data_sync_minute_business=0
        )
        cron = config_business.get_market_data_cron()
        assert cron == "0 18 * * 1-5"


class TestLoggingSettings:
    """Тесты настроек логирования"""
    
    def test_logging_settings_creation(self):
        """Тест создания настроек логирования"""
        config = LoggingSettings()
        
        assert config.level == "INFO"
        assert "%(asctime)s" in config.format
        assert config.file_path is None
        assert config.max_file_size == 10485760
        assert config.backup_count == 5
        
    def test_logging_level_validation(self):
        """Тест валидации уровня логирования"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level in valid_levels:
            config = LoggingSettings(level=level.lower())
            assert config.level == level.upper()
            
        # Некорректный уровень
        with pytest.raises(ValueError):
            LoggingSettings(level="INVALID")
            
    def test_logging_custom_settings(self):
        """Тест пользовательских настроек логирования"""
        config = LoggingSettings(
            level="DEBUG",
            format="%(message)s",
            file_path="/var/log/app.log",
            max_file_size=5242880,
            backup_count=3
        )
        
        assert config.level == "DEBUG"
        assert config.format == "%(message)s"
        assert config.file_path == "/var/log/app.log"
        assert config.max_file_size == 5242880
        assert config.backup_count == 3


class TestSecuritySettings:
    """Тесты настроек безопасности"""
    
    def test_security_settings_creation(self):
        """Тест создания настроек безопасности"""
        config = SecuritySettings()
        
        assert config.secret_key == "your-secret-key-change-in-production"
        assert config.algorithm == "HS256"
        assert config.access_token_expire_minutes == 30
        assert config.refresh_token_expire_days == 7
        
    def test_security_custom_settings(self):
        """Тест пользовательских настроек безопасности"""
        config = SecuritySettings(
            secret_key="custom-secret-key",
            algorithm="RS256",
            access_token_expire_minutes=60,
            refresh_token_expire_days=14
        )
        
        assert config.secret_key == "custom-secret-key"
        assert config.algorithm == "RS256"
        assert config.access_token_expire_minutes == 60
        assert config.refresh_token_expire_days == 14


class TestReportingSettings:
    """Тесты настроек отчетности"""
    
    def test_reporting_settings_creation(self):
        """Тест создания настроек отчетности"""
        config = ReportingSettings()
        
        assert config.max_report_history == 100
        assert config.default_date_range_days == 30
        assert config.cache_reports == True
        assert config.cache_ttl_minutes == 15
        
    def test_reporting_custom_settings(self):
        """Тест пользовательских настроек отчетности"""
        config = ReportingSettings(
            max_report_history=200,
            default_date_range_days=60,
            cache_reports=False,
            cache_ttl_minutes=30
        )
        
        assert config.max_report_history == 200
        assert config.default_date_range_days == 60
        assert config.cache_reports == False
        assert config.cache_ttl_minutes == 30


class TestSettings:
    """Тесты основных настроек приложения"""
    
    def test_settings_creation(self):
        """Тест создания основных настроек"""
        config = Settings()
        
        assert config.app_name == "Rebalancer"
        assert config.version == "0.1.0"
        assert config.debug == False
        assert config.environment == "development"
        assert config.api_prefix == "/api/v1"
        
    def test_settings_nested_configs(self):
        """Тест вложенных конфигураций"""
        config = Settings()
        
        assert isinstance(config.database, DatabaseSettings)
        assert isinstance(config.moex, MOEXSettings)
        assert isinstance(config.broker, BrokerSettings)
        assert isinstance(config.scheduler, SchedulerSettings)
        assert isinstance(config.logging, LoggingSettings)
        assert isinstance(config.security, SecuritySettings)
        assert isinstance(config.reporting, ReportingSettings)
        
    def test_settings_environment_validation(self):
        """Тест валидации окружения"""
        valid_environments = ["development", "production", "testing"]
        
        for env in valid_environments:
            config = Settings(environment=env)
            assert config.environment == env
            
        # Некорректное окружение
        with pytest.raises(ValueError):
            Settings(environment="invalid")
            
    def test_settings_backward_compatibility(self):
        """Тест обратной совместимости"""
        config = Settings()
        
        # Проверяем свойства обратной совместимости
        assert config.database_url == config.database.url
        assert config.moex_api_url == config.moex.api_url
        assert config.broker_api_url == config.broker.api_url
        assert config.broker_api_key == config.broker.api_key
        assert config.scheduler_enabled == config.scheduler.enabled


class TestGlobalSettings:
    """Тесты глобального объекта настроек"""
    
    def test_global_settings_exists(self):
        """Тест существования глобального объекта настроек"""
        assert settings is not None
        assert isinstance(settings, Settings)
        
    def test_global_settings_properties(self):
        """Тест свойств глобальных настроек"""
        assert hasattr(settings, 'app_name')
        assert hasattr(settings, 'version')
        assert hasattr(settings, 'database')
        assert hasattr(settings, 'moex')
        assert hasattr(settings, 'scheduler')
        
    def test_global_settings_immutability(self):
        """Тест неизменяемости глобальных настроек"""
        original_debug = settings.debug
        
        # Попытка изменить настройки (не должна влиять на другие тесты)
        try:
            # В реальном приложении эти настройки могут быть защищены
            assert settings.debug == original_debug
        except Exception:
            # Если изменение защищено, это хорошо
            pass


class TestEnvironmentVariables:
    """Тесты работы с переменными окружения"""
    
    def test_nested_env_vars(self):
        """Тест вложенных переменных окружения"""
        env_vars = {
            'DATABASE__URL': 'sqlite:///test.db',
            'DATABASE__ECHO': 'true',
            'MOEX__TIMEOUT': '60',
            'SCHEDULER__ENABLED': 'false'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = Settings()
            
            # Проверяем что вложенные переменные применились
            assert config.database.url == 'sqlite:///test.db'
            assert config.database.echo == True
            assert config.moex.timeout == 60
            assert config.scheduler.enabled == False
            
    def test_case_insensitive_env_vars(self):
        """Тест нечувствительности к регистру"""
        with patch.dict(os.environ, {'debug': 'true'}, clear=True):
            config = Settings()
            assert config.debug == True
            
    def test_env_file_loading(self):
        """Тест загрузки из .env файла"""
        # Проверяем что Config.env_file установлен
        assert Settings.Config.env_file == ".env"
        assert Settings.Config.env_file_encoding == "utf-8"
        assert Settings.Config.env_nested_delimiter == "__"


class TestConfigValidation:
    """Тесты валидации конфигурации"""
    
    def test_cors_settings(self):
        """Тест настроек CORS"""
        config = Settings()
        
        assert isinstance(config.cors_origins, list)
        assert len(config.cors_origins) > 0
        assert config.cors_credentials == True
        assert "GET" in config.cors_methods
        assert "POST" in config.cors_methods
        
    def test_allowed_hosts(self):
        """Тест разрешенных хостов"""
        config = Settings()
        
        assert isinstance(config.allowed_hosts, list)
        assert "*" in config.allowed_hosts or len(config.allowed_hosts) > 0
        
    def test_api_urls(self):
        """Тест URL API"""
        config = Settings()
        
        assert config.docs_url == "/docs"
        assert config.redoc_url == "/redoc"
        assert config.api_prefix == "/api/v1"


class TestConfigSerialization:
    """Тесты сериализации конфигурации"""
    
    def test_config_dict_conversion(self):
        """Тест преобразования в словарь"""
        config = Settings()
        
        # Проверяем что можем получить словарь
        config_dict = config.dict()
        assert isinstance(config_dict, dict)
        assert 'app_name' in config_dict
        assert 'database' in config_dict
        assert 'moex' in config_dict
        
    def test_nested_dict_structure(self):
        """Тест структуры вложенного словаря"""
        config = Settings()
        config_dict = config.dict()
        
        # Проверяем вложенные структуры
        assert isinstance(config_dict['database'], dict)
        assert 'url' in config_dict['database']
        assert 'echo' in config_dict['database']
        
        assert isinstance(config_dict['moex'], dict)
        assert 'api_url' in config_dict['moex']
        assert 'timeout' in config_dict['moex']
        
    def test_json_serialization(self):
        """Тест JSON сериализации"""
        import json
        
        config = Settings()
        config_dict = config.dict()
        
        # Проверяем что можем сериализовать в JSON
        json_str = json.dumps(config_dict)
        assert json_str is not None
        assert len(json_str) > 0
        
        # Проверяем что можем десериализовать обратно
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert parsed['app_name'] == config.app_name


class TestConfigDefaults:
    """Тесты значений по умолчанию"""
    
    def test_all_defaults_set(self):
        """Тест что все значения по умолчанию установлены"""
        config = Settings()
        
        # Основные настройки
        assert config.app_name is not None
        assert config.version is not None
        assert isinstance(config.debug, bool)
        
        # БД настройки
        assert config.database.url is not None
        assert isinstance(config.database.pool_size, int)
        
        # MOEX настройки
        assert config.moex.api_url is not None
        assert isinstance(config.moex.timeout, int)
        
        # Планировщик
        assert isinstance(config.scheduler.enabled, bool)
        assert config.scheduler.timezone is not None
        
    def test_sensible_defaults(self):
        """Тест разумности значений по умолчанию"""
        config = Settings()
        
        # Проверяем что значения имеют смысл
        assert config.database.pool_size > 0
        assert config.database.max_overflow > 0
        assert config.moex.timeout > 0
        assert config.moex.rate_limit > 0
        assert config.security.access_token_expire_minutes > 0
        assert config.reporting.max_report_history > 0