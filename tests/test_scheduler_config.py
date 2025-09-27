import pytest
from unittest.mock import Mock, patch
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import SchedulerSettings
from app.scheduler import setup_scheduler


class TestSchedulerConfiguration:
    """Тесты настройки планировщика"""

    def test_24_7_mode_default(self):
        """Тест дефолтного режима 24/7"""
        settings = SchedulerSettings()
        assert settings.trading_mode == "24/7"
        assert settings.market_data_sync_hour_24_7 == 19
        assert settings.market_data_sync_minute_24_7 == 0

        # Проверяем cron выражение для 24/7
        cron = settings.get_market_data_cron()
        assert cron == "0 19 * * *"  # каждый день в 19:00

    def test_business_days_mode(self):
        """Тест режима рабочих дней"""
        settings = SchedulerSettings(trading_mode="business_days")
        assert settings.trading_mode == "business_days"

        # Проверяем cron выражение для рабочих дней
        cron = settings.get_market_data_cron()
        assert cron == "0 18 * * 1-5"  # пн-пт в 18:00

    def test_custom_hours_24_7(self):
        """Тест кастомного времени для режима 24/7"""
        settings = SchedulerSettings(
            trading_mode="24/7",
            market_data_sync_hour_24_7=12,
            market_data_sync_minute_24_7=30,
        )

        cron = settings.get_market_data_cron()
        assert cron == "30 12 * * *"  # каждый день в 12:30

    def test_custom_hours_business_days(self):
        """Тест кастомного времени для рабочих дней"""
        settings = SchedulerSettings(
            trading_mode="business_days",
            market_data_sync_hour_business=9,
            market_data_sync_minute_business=15,
        )

        cron = settings.get_market_data_cron()
        assert cron == "15 9 * * 1-5"  # пн-пт в 9:15

    def test_invalid_trading_mode(self):
        """Тест валидации неверного режима торгов"""
        with pytest.raises(ValueError, match="Режим торгов должен быть одним из"):
            SchedulerSettings(trading_mode="invalid_mode")

    @patch("app.scheduler.settings")
    def test_setup_scheduler_24_7(self, mock_settings):
        """Тест настройки планировщика в режиме 24/7"""
        # Мокаем настройки
        mock_settings.scheduler = SchedulerSettings(trading_mode="24/7")

        # Создаем мок планировщика
        scheduler = Mock(spec=AsyncIOScheduler)

        # Вызываем setup_scheduler
        setup_scheduler(scheduler)

        # Проверяем что add_job был вызван с правильными параметрами
        scheduler.add_job.assert_called_once()
        call_args = scheduler.add_job.call_args

        # Проверяем имя задачи
        assert call_args.kwargs["name"] == "Daily Market Data Update"
        assert call_args.kwargs["id"] == "daily_market_data_update"

    @patch("app.scheduler.settings")
    def test_setup_scheduler_business_days(self, mock_settings):
        """Тест настройки планировщика в режиме рабочих дней"""
        # Мокаем настройки
        mock_settings.scheduler = SchedulerSettings(trading_mode="business_days")

        # Создаем мок планировщика
        scheduler = Mock(spec=AsyncIOScheduler)

        # Вызываем setup_scheduler
        setup_scheduler(scheduler)

        # Проверяем что add_job был вызван
        scheduler.add_job.assert_called_once()
        call_args = scheduler.add_job.call_args

        # Проверяем имя задачи
        assert call_args.kwargs["name"] == "Daily Market Data Update"
        assert call_args.kwargs["id"] == "daily_market_data_update"
