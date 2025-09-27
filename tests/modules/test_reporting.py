"""Тесты для модуля отчетности"""

import pytest
from datetime import datetime, date
from decimal import Decimal

from app.storage import DataManager
from app.modules.portfolio.models import Portfolio, Position
from app.modules.marketdata.models import Security, Quote
from app.modules.reporting.service import ReportingService
from app.modules.reporting.models import TransactionType


class TestReportingService:
    """Тесты для ReportingService"""

    @pytest.fixture
    def data_manager(self):
        """Fixture для DataManager"""
        dm = DataManager()
        dm.clear_all()
        return dm

    @pytest.fixture
    def reporting_service(self, data_manager):
        """Fixture для ReportingService"""
        return ReportingService(data_manager)

    @pytest.fixture
    def sample_data(self, data_manager):
        """Fixture с тестовыми данными"""
        # Создаем ценные бумаги
        security1 = Security(secid="SBER", name="Сбер Банк", isin="RU0009029540")
        security2 = Security(secid="GAZP", name="Газпром", isin="RU0007661625")
        data_manager.add_security(security1)
        data_manager.add_security(security2)

        # Создаем портфель
        portfolio = Portfolio(
            id=data_manager.get_next_portfolio_id(),
            name="Тестовый портфель",
            description="Портфель для тестирования",
        )
        data_manager.add_portfolio(portfolio)

        # Создаем позиции
        position1 = Position(
            id=data_manager.get_next_position_id(),
            portfolio_id=portfolio.id,
            secid="SBER",
            quantity=Decimal("100"),
            avg_price=Decimal("200.50"),
        )
        position2 = Position(
            id=data_manager.get_next_position_id(),
            portfolio_id=portfolio.id,
            secid="GAZP",
            quantity=Decimal("50"),
            avg_price=Decimal("150.00"),
        )
        data_manager.add_position(position1)
        data_manager.add_position(position2)

        # Добавляем котировки
        quote1 = Quote(
            secid="SBER",
            timestamp=datetime.now(),
            price=Decimal("220.00"),
            volume=Decimal("1000"),
        )
        quote2 = Quote(
            secid="GAZP",
            timestamp=datetime.now(),
            price=Decimal("140.00"),
            volume=Decimal("500"),
        )
        data_manager.add_quote(quote1)
        data_manager.add_quote(quote2)

        return {
            "portfolio": portfolio,
            "positions": [position1, position2],
            "securities": [security1, security2],
            "quotes": [quote1, quote2],
        }


class TestTransactionOperations(TestReportingService):
    """Тесты операций с транзакциями"""

    def test_create_transaction(self, reporting_service, sample_data):
        """Тест создания транзакции"""
        portfolio = sample_data["portfolio"]

        transaction = reporting_service.create_transaction(
            portfolio_id=portfolio.id,
            secid="SBER",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("10"),
            price=Decimal("200.00"),
            commission=Decimal("5.00"),
            notes="Тестовая покупка",
        )

        assert transaction.id == 1
        assert transaction.portfolio_id == portfolio.id
        assert transaction.secid == "SBER"
        assert transaction.transaction_type == TransactionType.BUY
        assert transaction.quantity == Decimal("10")
        assert transaction.price == Decimal("200.00")
        assert transaction.commission == Decimal("5.00")
        assert transaction.total_amount == Decimal("2000.00")
        assert transaction.total_cost == Decimal("2005.00")  # с комиссией

    def test_get_transactions_with_filters(self, reporting_service, sample_data):
        """Тест получения транзакций с фильтрами"""
        portfolio = sample_data["portfolio"]

        # Создаем несколько транзакций
        reporting_service.create_transaction(
            portfolio_id=portfolio.id,
            secid="SBER",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("10"),
            price=Decimal("200.00"),
            timestamp=datetime(2024, 1, 15),
        )

        reporting_service.create_transaction(
            portfolio_id=portfolio.id,
            secid="GAZP",
            transaction_type=TransactionType.SELL,
            quantity=Decimal("5"),
            price=Decimal("150.00"),
            timestamp=datetime(2024, 1, 20),
        )

        # Тест фильтрации по портфелю
        transactions = reporting_service.get_transactions(portfolio_id=portfolio.id)
        assert len(transactions) == 2

        # Тест фильтрации по датам
        transactions = reporting_service.get_transactions(
            portfolio_id=portfolio.id,
            start_date=date(2024, 1, 16),
            end_date=date(2024, 1, 25),
        )
        assert len(transactions) == 1
        assert transactions[0].secid == "GAZP"


class TestPortfolioReport(TestReportingService):
    """Тесты отчета по портфелю"""

    def test_generate_portfolio_report(self, reporting_service, sample_data):
        """Тест генерации отчета по портфелю"""
        portfolio = sample_data["portfolio"]

        report = reporting_service.generate_portfolio_report(
            portfolio_id=portfolio.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        assert report.portfolio_id == portfolio.id
        assert report.portfolio_name == portfolio.name
        assert len(report.positions) == 2

        # Проверяем расчеты
        assert report.total_cost == Decimal("27550.00")  # 100*200.50 + 50*150.00
        assert report.total_value == Decimal("29000.00")  # 100*220.00 + 50*140.00
        assert report.total_unrealized_pnl == Decimal("1450.00")  # 29000 - 27550

        # Проверяем позиции
        sber_position = next(p for p in report.positions if p.secid == "SBER")
        assert sber_position.quantity == Decimal("100")
        assert sber_position.current_price == Decimal("220.00")
        assert sber_position.market_value == Decimal("22000.00")
        assert sber_position.unrealized_pnl == Decimal("1950.00")  # (220-200.50)*100

    def test_portfolio_report_nonexistent_portfolio(self, reporting_service):
        """Тест отчета для несуществующего портфеля"""
        with pytest.raises(ValueError, match="Portfolio 999 not found"):
            reporting_service.generate_portfolio_report(
                portfolio_id=999,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )


class TestTransactionReport(TestReportingService):
    """Тесты отчета по транзакциям"""

    def test_generate_transaction_report(self, reporting_service, sample_data):
        """Тест генерации отчета по транзакциям"""
        portfolio = sample_data["portfolio"]

        # Создаем транзакции
        reporting_service.create_transaction(
            portfolio_id=portfolio.id,
            secid="SBER",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("10"),
            price=Decimal("200.00"),
            commission=Decimal("5.00"),
            timestamp=datetime(2024, 6, 15),  # Указываем дату в 2024 году
        )

        reporting_service.create_transaction(
            portfolio_id=portfolio.id,
            secid="SBER",
            transaction_type=TransactionType.SELL,
            quantity=Decimal("5"),
            price=Decimal("220.00"),
            commission=Decimal("3.00"),
            timestamp=datetime(2024, 6, 20),  # Указываем дату в 2024 году
        )

        report = reporting_service.generate_transaction_report(
            portfolio_id=portfolio.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )

        assert report.portfolio_id == portfolio.id
        assert len(report.transactions) == 2
        assert report.total_transactions == 2
        assert report.total_buy_amount == Decimal("2000.00")
        assert report.total_sell_amount == Decimal("1100.00")
        assert report.total_commission == Decimal("8.00")

        # Проверяем сводку
        assert len(report.summary_by_security) == 1
        sber_summary = report.summary_by_security[0]
        assert sber_summary.secid == "SBER"
        assert sber_summary.total_buy_quantity == Decimal("10")
        assert sber_summary.total_sell_quantity == Decimal("5")
        assert sber_summary.net_quantity == Decimal("5")


class TestPnLReport(TestReportingService):
    """Тесты отчета P&L"""

    def test_generate_pnl_report(self, reporting_service, sample_data):
        """Тест генерации отчета P&L"""
        portfolio = sample_data["portfolio"]

        # Создаем несколько транзакций для расчета реализованной прибыли
        reporting_service.create_transaction(
            portfolio_id=portfolio.id,
            secid="SBER",
            transaction_type=TransactionType.SELL,
            quantity=Decimal("10"),
            price=Decimal("250.00"),  # Продаем дороже средней цены
        )

        report = reporting_service.generate_pnl_report(
            portfolio_id=portfolio.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )

        assert report.portfolio_id == portfolio.id
        assert len(report.pnl_entries) >= 1

        # Находим запись по SBER
        sber_entry = next((e for e in report.pnl_entries if e.secid == "SBER"), None)
        assert sber_entry is not None
        assert sber_entry.quantity_held == Decimal("100")  # Изначальная позиция
        assert sber_entry.avg_cost == Decimal("200.50")
        assert sber_entry.current_price == Decimal("220.00")
        assert sber_entry.unrealized_pnl == Decimal("1950.00")  # (220-200.50)*100

    def test_pnl_report_best_worst_performers(self, reporting_service, sample_data):
        """Тест определения лучших и худших исполнителей"""
        portfolio = sample_data["portfolio"]

        report = reporting_service.generate_pnl_report(
            portfolio_id=portfolio.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )

        assert len(report.best_performers) > 0
        assert len(report.worst_performers) > 0

        # SBER должен быть лучшим исполнителем (растет с 200.50 до 220.00)
        best_performer = report.best_performers[0]
        assert best_performer.secid == "SBER"
        assert best_performer.total_pnl > 0


class TestReportingEdgeCases(TestReportingService):
    """Тесты граничных случаев"""

    def test_empty_portfolio_report(self, reporting_service, data_manager):
        """Тест отчета для пустого портфеля"""
        portfolio = Portfolio(
            id=data_manager.get_next_portfolio_id(), name="Пустой портфель"
        )
        data_manager.add_portfolio(portfolio)

        report = reporting_service.generate_portfolio_report(
            portfolio_id=portfolio.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        assert len(report.positions) == 0
        assert report.total_value == Decimal("0")
        assert report.total_cost == Decimal("0")
        assert report.total_unrealized_pnl == Decimal("0")

    def test_transaction_without_commission(self, reporting_service, sample_data):
        """Тест транзакции без комиссии"""
        portfolio = sample_data["portfolio"]

        transaction = reporting_service.create_transaction(
            portfolio_id=portfolio.id,
            secid="SBER",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("10"),
            price=Decimal("200.00"),
            # commission не указываем
        )

        assert transaction.commission is None
        assert transaction.total_cost == transaction.total_amount  # Без комиссии

    def test_position_without_current_price(self, reporting_service, data_manager):
        """Тест позиции без текущей цены"""
        # Создаем портфель и позицию без котировки
        portfolio = Portfolio(
            id=data_manager.get_next_portfolio_id(), name="Тест портфель"
        )
        data_manager.add_portfolio(portfolio)

        security = Security(secid="TEST", name="Тест бумага")
        data_manager.add_security(security)

        position = Position(
            id=data_manager.get_next_position_id(),
            portfolio_id=portfolio.id,
            secid="TEST",
            quantity=Decimal("100"),
            avg_price=Decimal("100.00"),
        )
        data_manager.add_position(position)

        report = reporting_service.generate_portfolio_report(
            portfolio_id=portfolio.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        test_position = report.positions[0]
        assert test_position.current_price is None
        assert test_position.market_value is None
        assert test_position.unrealized_pnl is None
