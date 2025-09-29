"""Тесты для модуля scheduler"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.scheduler import setup_scheduler, daily_market_data_update
from app.config import settings


class TestSchedulerSetup:
    """Тесты для функции setup_scheduler"""
    
    @patch('app.scheduler.logger')
    def test_setup_scheduler_basic(self, mock_logger):
        """Базовый тест настройки scheduler"""
        mock_scheduler = MagicMock(spec=AsyncIOScheduler)
        
        # Мокаем настройки
        with patch('app.scheduler.settings') as mock_settings:
            mock_settings.scheduler.get_market_data_cron.return_value = '0 19 * * *'
            mock_settings.scheduler.trading_mode = '24/7'
            mock_settings.scheduler.timezone = 'Europe/Moscow'
            
            setup_scheduler(mock_scheduler)
            
            # Проверяем что job был добавлен
            mock_scheduler.add_job.assert_called_once()
            call_args = mock_scheduler.add_job.call_args
            
            # Проверяем параметры job
            assert call_args[0][0] == daily_market_data_update
            assert call_args[1]['id'] == 'daily_market_data_update'
            assert call_args[1]['name'] == 'Daily Market Data Update'
            assert call_args[1]['replace_existing'] is True
            
    @patch('app.scheduler.logger')
    def test_setup_scheduler_different_trading_modes(self, mock_logger):
        """Тест настройки scheduler для разных режимов торгов"""
        mock_scheduler = MagicMock(spec=AsyncIOScheduler)
        
        # Тест для режима 'market_hours'
        with patch('app.scheduler.settings') as mock_settings:
            mock_settings.scheduler.get_market_data_cron.return_value = '0 20 * * 1-5'
            mock_settings.scheduler.trading_mode = 'market_hours'
            mock_settings.scheduler.timezone = 'Europe/Moscow'
            
            setup_scheduler(mock_scheduler)
            
            # Проверяем что логи содержат правильный режим
            mock_logger.info.assert_any_call("Настройка планировщика в режиме 'market_hours'")
            mock_logger.info.assert_any_call("Расписание синхронизации данных: 0 20 * * 1-5")


class TestDailyMarketDataUpdate:
    """Тесты для функции daily_market_data_update"""
    
    @pytest.mark.asyncio
    @patch('app.scheduler.logger')
    @patch('app.scheduler.DataManager')
    @patch('app.scheduler.MarketDataService')
    async def test_daily_market_data_update_success(self, mock_market_service_class, mock_data_manager_class, mock_logger):
        """Тест успешного выполнения обновления данных"""
        # Настраиваем моки
        mock_data_manager = AsyncMock()
        mock_data_manager_class.return_value = mock_data_manager
        
        mock_market_service = AsyncMock()
        mock_market_service_class.return_value = mock_market_service
        
        # Мокаем securities
        mock_securities = [
            MagicMock(secid='SBER'),
            MagicMock(secid='GAZP'),
        ]
        mock_market_service.get_securities.return_value = mock_securities
        mock_market_service.sync_quotes_for_security.return_value = 10
        
        with patch('app.scheduler.settings') as mock_settings:
            mock_settings.scheduler.trading_mode = '24/7'
            await daily_market_data_update()
            
        # Проверяем что сервис был создан
        mock_data_manager_class.assert_called_once()
        mock_market_service_class.assert_called_once_with(mock_data_manager)
        
        # Проверяем что данные загружались
        mock_market_service.get_securities.assert_called()
        
        # Проверяем что обновления по каждому инструменту вызывались
        assert mock_market_service.sync_quotes_for_security.call_count == 2
        
        # Проверяем что сервис был закрыт
        mock_market_service.close.assert_called_once()
        
    @pytest.mark.asyncio
    @patch('app.scheduler.logger')
    @patch('app.scheduler.DataManager')
    @patch('app.scheduler.MarketDataService')
    async def test_daily_market_data_update_no_securities_loads_from_moex(self, mock_market_service_class, mock_data_manager_class, mock_logger):
        """Тест обновления когда нет локальных данных - загрузка с MOEX"""
        mock_data_manager = AsyncMock()
        mock_data_manager_class.return_value = mock_data_manager
        
        mock_market_service = AsyncMock()
        mock_market_service_class.return_value = mock_market_service
        
        # Первый вызов возвращает пустой список, второй - данные
        mock_securities = [MagicMock(secid='SBER')]
        mock_market_service.get_securities.side_effect = [[], mock_securities]
        mock_market_service.sync_securities_from_moex.return_value = 100
        mock_market_service.sync_quotes_for_security.return_value = 5
        
        with patch('app.scheduler.settings') as mock_settings:
            mock_settings.scheduler.trading_mode = '24/7'
            await daily_market_data_update()
            
        # Проверяем что данные загружались с MOEX
        mock_market_service.sync_securities_from_moex.assert_called_once()
        mock_logger.info.assert_any_call("No securities found in local storage, loading from MOEX...")
        mock_logger.info.assert_any_call("Loaded 100 securities from MOEX")
        
    @pytest.mark.asyncio  
    @patch('app.scheduler.logger')
    @patch('app.scheduler.DataManager')
    @patch('app.scheduler.MarketDataService')
    async def test_daily_market_data_update_no_securities_after_moex(self, mock_market_service_class, mock_data_manager_class, mock_logger):
        """Тест когда не удается загрузить данные даже с MOEX"""
        mock_data_manager = AsyncMock()
        mock_data_manager_class.return_value = mock_data_manager
        
        mock_market_service = AsyncMock()
        mock_market_service_class.return_value = mock_market_service
        
        # Всегда возвращаем пустой список
        mock_market_service.get_securities.return_value = []
        mock_market_service.sync_securities_from_moex.return_value = 0
        
        with patch('app.scheduler.settings') as mock_settings:
            mock_settings.scheduler.trading_mode = '24/7'
            await daily_market_data_update()
            
        # Проверяем что была ошибка
        mock_logger.error.assert_any_call("Failed to load securities data")
        
        # Quotes не должны обновляться
        mock_market_service.sync_quotes_for_security.assert_not_called()
        
    @pytest.mark.asyncio
    @patch('app.scheduler.logger')
    @patch('app.scheduler.DataManager')
    @patch('app.scheduler.MarketDataService')
    async def test_daily_market_data_update_with_security_error(self, mock_market_service_class, mock_data_manager_class, mock_logger):
        """Тест обработки ошибок при обновлении отдельного инструмента"""
        mock_data_manager = AsyncMock()
        mock_data_manager_class.return_value = mock_data_manager
        
        mock_market_service = AsyncMock()
        mock_market_service_class.return_value = mock_market_service
        
        mock_securities = [
            MagicMock(secid='SBER'),
            MagicMock(secid='GAZP'),
        ]
        mock_market_service.get_securities.return_value = mock_securities
        
        # Первый security вызывает ошибку, второй - успешно
        mock_market_service.sync_quotes_for_security.side_effect = [
            Exception("Network error"), 
            15
        ]
        
        with patch('app.scheduler.settings') as mock_settings:
            mock_settings.scheduler.trading_mode = '24/7'
            await daily_market_data_update()
            
        # Проверяем что ошибка была залогирована
        mock_logger.error.assert_any_call("Failed to update historical data for SBER: Network error")
        
        # Проверяем что второй security все равно обработался
        assert mock_market_service.sync_quotes_for_security.call_count == 2
        
    @pytest.mark.asyncio
    @patch('app.scheduler.logger')
    @patch('app.scheduler.DataManager')
    @patch('app.scheduler.MarketDataService')
    @patch('traceback.print_exc')
    async def test_daily_market_data_update_general_exception(self, mock_print_exc, mock_market_service_class, mock_data_manager_class, mock_logger):
        """Тест обработки общих ошибок"""
        mock_data_manager_class.side_effect = Exception("Database connection failed")
        
        with patch('app.scheduler.settings') as mock_settings:
            mock_settings.scheduler.trading_mode = '24/7'
            await daily_market_data_update()
            
        # Проверяем что ошибка была залогирована
        mock_logger.error.assert_any_call("Market data update failed: Database connection failed")
        mock_print_exc.assert_called_once()


class TestSchedulerLogging:
    """Тесты логирования scheduler"""
    
    @patch('app.scheduler.logger')
    def test_scheduler_logging_messages(self, mock_logger):
        """Тест сообщений логирования в scheduler"""
        mock_scheduler = MagicMock(spec=AsyncIOScheduler)
        
        with patch('app.scheduler.settings') as mock_settings:
            mock_settings.scheduler.get_market_data_cron.return_value = '0 19 * * *'
            mock_settings.scheduler.trading_mode = '24/7'
            mock_settings.scheduler.timezone = 'Europe/Moscow'
            
            setup_scheduler(mock_scheduler)
            
        # Проверяем что логи вызываются с правильными сообщениями
        expected_calls = [
            "Настройка планировщика в режиме '24/7'",
            "Расписание синхронизации данных: 0 19 * * *"
        ]
        
        for expected_msg in expected_calls:
            mock_logger.info.assert_any_call(expected_msg)