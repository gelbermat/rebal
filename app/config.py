import os
from typing import Optional, List
from pathlib import Path

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Настройки базы данных"""

    url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/rebalancer",
        description="URL подключения к базе данных",
    )
    echo: bool = Field(default=False, description="Логирование SQL запросов")
    pool_size: int = Field(default=10, description="Размер пула соединений")
    max_overflow: int = Field(default=20, description="Максимальное переполнение пула")


class MOEXSettings(BaseSettings):
    """Настройки MOEX API"""

    api_url: str = Field(default="https://iss.moex.com", description="URL MOEX API")
    timeout: int = Field(default=30, description="Таймаут запросов в секундах")
    rate_limit: int = Field(default=100, description="Лимит запросов в минуту")
    retries: int = Field(default=3, description="Количество повторных попыток")

    @validator("api_url")
    def validate_api_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("API URL должен начинаться с http:// или https://")
        return v


class BrokerSettings(BaseSettings):
    """Настройки брокера"""

    api_url: Optional[str] = Field(default=None, description="URL API брокера")
    api_key: Optional[str] = Field(default=None, description="API ключ брокера")
    api_secret: Optional[str] = Field(default=None, description="Секретный ключ API")
    account_id: Optional[str] = Field(default=None, description="ID торгового счета")
    sandbox_mode: bool = Field(default=True, description="Режим песочницы")


class SchedulerSettings(BaseSettings):
    """Настройки планировщика"""

    enabled: bool = Field(default=True, description="Включить планировщик")
    timezone: str = Field(default="Europe/Moscow", description="Часовой пояс")

    # Новые настройки для режима работы
    trading_mode: str = Field(
        default="24/7",
        description="Режим торгов: '24/7' для круглосуточной работы или 'business_days' для пн-пт",
    )

    # Настройки для режима 24/7
    market_data_sync_hour_24_7: int = Field(
        default=19,
        description="Час для синхронизации данных в режиме 24/7 (каждый день)",
    )
    market_data_sync_minute_24_7: int = Field(
        default=0, description="Минута для синхронизации данных в режиме 24/7"
    )

    # Настройки для режима рабочих дней
    market_data_sync_hour_business: int = Field(
        default=18, description="Час для синхронизации данных в режиме рабочих дней"
    )
    market_data_sync_minute_business: int = Field(
        default=0, description="Минута для синхронизации данных в режиме рабочих дней"
    )

    # Устаревшие настройки (для обратной совместимости)
    market_data_sync_cron: str = Field(
        default="0 19 * * *",
        description="Расписание синхронизации данных (deprecated, используйте trading_mode)",
    )
    rebalancing_cron: str = Field(
        default="0 10 * * 1",
        description="Расписание ребалансировки (понедельник в 10:00)",
    )

    @validator("trading_mode")
    def validate_trading_mode(cls, v):
        valid_modes = ["24/7", "business_days"]
        if v not in valid_modes:
            raise ValueError(f"Режим торгов должен быть одним из: {valid_modes}")
        return v

    def get_market_data_cron(self) -> str:
        """Возвращает cron выражение для синхронизации данных в зависимости от режима"""
        if self.trading_mode == "24/7":
            return f"{self.market_data_sync_minute_24_7} {self.market_data_sync_hour_24_7} * * *"
        else:  # business_days
            return f"{self.market_data_sync_minute_business} {self.market_data_sync_hour_business} * * 1-5"


class LoggingSettings(BaseSettings):
    """Настройки логирования"""

    level: str = Field(default="INFO", description="Уровень логирования")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Формат лог-сообщений",
    )
    file_path: Optional[str] = Field(default=None, description="Путь к файлу логов")
    max_file_size: int = Field(
        default=10485760, description="Максимальный размер файла логов (10MB)"
    )
    backup_count: int = Field(default=5, description="Количество архивных файлов логов")

    @validator("level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(
                f"Уровень логирования должен быть одним из: {valid_levels}"
            )
        return v.upper()


class SecuritySettings(BaseSettings):
    """Настройки безопасности"""

    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Секретный ключ для подписи JWT токенов",
    )
    algorithm: str = Field(default="HS256", description="Алгоритм для JWT")
    access_token_expire_minutes: int = Field(
        default=30, description="Время жизни access токена в минутах"
    )
    refresh_token_expire_days: int = Field(
        default=7, description="Время жизни refresh токена в днях"
    )


class ReportingSettings(BaseSettings):
    """Настройки модуля отчетности"""

    max_report_history: int = Field(
        default=100, description="Максимальное количество сохраняемых отчетов"
    )
    default_date_range_days: int = Field(
        default=30, description="Диапазон дат по умолчанию для отчетов"
    )
    cache_reports: bool = Field(default=True, description="Кэшировать отчеты")
    cache_ttl_minutes: int = Field(default=15, description="TTL кэша отчетов в минутах")


class Settings(BaseSettings):
    """Основные настройки приложения"""

    # Основные настройки
    app_name: str = Field(default="Rebalancer", description="Название приложения")
    version: str = Field(default="0.1.0", description="Версия приложения")
    debug: bool = Field(default=False, description="Режим отладки")
    environment: str = Field(
        default="development", description="Окружение (development/production)"
    )

    # API настройки
    api_prefix: str = Field(default="/api/v1", description="Префикс API")
    docs_url: str = Field(default="/docs", description="URL документации Swagger")
    redoc_url: str = Field(default="/redoc", description="URL документации ReDoc")
    allowed_hosts: List[str] = Field(default=["*"], description="Разрешенные хосты")

    # CORS настройки
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Разрешенные CORS origins",
    )
    cors_credentials: bool = Field(
        default=True, description="Разрешить CORS credentials"
    )
    cors_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Разрешенные HTTP методы для CORS",
    )
    cors_headers: List[str] = Field(
        default=["*"], description="Разрешенные заголовки для CORS"
    )

    # Подключаемые модули настроек
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    moex: MOEXSettings = Field(default_factory=MOEXSettings)
    broker: BrokerSettings = Field(default_factory=BrokerSettings)
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    reporting: ReportingSettings = Field(default_factory=ReportingSettings)

    # Обратная совместимость
    @property
    def database_url(self) -> str:
        """Обратная совместимость для database_url"""
        return self.database.url

    @property
    def moex_api_url(self) -> str:
        """Обратная совместимость для moex_api_url"""
        return self.moex.api_url

    @property
    def broker_api_url(self) -> Optional[str]:
        """Обратная совместимость для broker_api_url"""
        return self.broker.api_url

    @property
    def broker_api_key(self) -> Optional[str]:
        """Обратная совместимость для broker_api_key"""
        return self.broker.api_key

    @property
    def scheduler_enabled(self) -> bool:
        """Обратная совместимость для scheduler_enabled"""
        return self.scheduler.enabled

    @validator("environment")
    def validate_environment(cls, v):
        valid_environments = ["development", "production", "testing"]
        if v not in valid_environments:
            raise ValueError(f"Environment должен быть одним из: {valid_environments}")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"  # Для вложенных настроек: DATABASE__URL
        case_sensitive = False


settings = Settings()
