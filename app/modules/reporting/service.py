"""Сервис для генерации отчетов и аналитики"""

import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from collections import defaultdict

from app.storage import DataManager
from app.modules.portfolio.models import Portfolio, Position
from app.modules.marketdata.models import Security, Quote
from .models import (
    Transaction,
    TransactionType,
    PortfolioReport,
    TransactionReport,
    PnLReport,
    PortfolioSnapshot,
    TransactionSummary,
    PnLEntry,
    ReportRequest,
    ReportType,
)


class ReportingService:
    """Сервис для создания отчетов и аналитики"""

    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager

    def create_transaction(
        self,
        portfolio_id: int,
        secid: str,
        transaction_type: TransactionType,
        quantity: Decimal,
        price: Decimal,
        timestamp: Optional[datetime] = None,
        commission: Optional[Decimal] = None,
        notes: Optional[str] = None,
    ) -> Transaction:
        """Создание новой транзакции"""
        transaction_id = self.data_manager.get_next_transaction_id()

        transaction = Transaction(
            id=transaction_id,
            portfolio_id=portfolio_id,
            secid=secid,
            transaction_type=transaction_type,
            quantity=quantity,
            price=price,
            timestamp=timestamp or datetime.now(),
            commission=commission,
            notes=notes,
        )

        self.data_manager.add_transaction(transaction)
        return transaction

    def get_transactions(
        self,
        portfolio_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Transaction]:
        """Получение транзакций с фильтрацией"""
        if portfolio_id is not None:
            transactions = self.data_manager.get_transactions_for_portfolio(
                portfolio_id
            )
        else:
            transactions = self.data_manager.get_all_transactions()

        # Фильтрация по датам
        if start_date or end_date:
            filtered_transactions = []
            for tx in transactions:
                tx_date = tx.timestamp.date()
                if start_date and tx_date < start_date:
                    continue
                if end_date and tx_date > end_date:
                    continue
                filtered_transactions.append(tx)
            return filtered_transactions

        return transactions

    def generate_portfolio_report(
        self,
        portfolio_id: int,
        start_date: date,
        end_date: date,
        include_performance_metrics: bool = True,
        top_holdings_limit: int = 10,
    ) -> PortfolioReport:
        """Генерация отчета по портфелю"""
        portfolio = self.data_manager.get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")

        report_id = str(uuid.uuid4())

        # Получаем позиции портфеля
        positions = self.data_manager.get_positions_for_portfolio(portfolio_id)
        portfolio_snapshots = []

        total_value = Decimal("0")
        total_cost = Decimal("0")
        total_unrealized_pnl = Decimal("0")

        for position in positions:
            security = self.data_manager.get_security(position.secid)
            security_name = security.name if security else position.secid

            # Получаем последнюю котировку
            latest_quote = self.data_manager.get_latest_quote(position.secid)
            current_price = latest_quote.price if latest_quote else None

            market_value = None
            unrealized_pnl = None
            if current_price:
                market_value = position.quantity * current_price
                unrealized_pnl = market_value - (position.quantity * position.avg_price)
                total_value += market_value
                total_unrealized_pnl += unrealized_pnl

            position_cost = position.quantity * position.avg_price
            total_cost += position_cost

            snapshot = PortfolioSnapshot(
                portfolio_id=portfolio_id,
                date=end_date,
                secid=position.secid,
                security_name=security_name,
                quantity=position.quantity,
                avg_cost=position.avg_price,
                current_price=current_price,
                market_value=market_value,
                unrealized_pnl=unrealized_pnl,
            )
            portfolio_snapshots.append(snapshot)

        # Вычисляем веса позиций
        if total_value > 0:
            for snapshot in portfolio_snapshots:
                if snapshot.market_value:
                    snapshot.weight_percent = (
                        snapshot.market_value / total_value
                    ) * 100

        # Получаем реализованную прибыль из транзакций
        total_realized_pnl = self._calculate_realized_pnl(
            portfolio_id, start_date, end_date
        )

        # Топ позиции
        top_holdings = sorted(
            [s for s in portfolio_snapshots if s.market_value],
            key=lambda x: x.market_value,
            reverse=True,
        )[:top_holdings_limit]

        # Распределение активов (простая группировка по первой букве)
        asset_allocation = self._calculate_asset_allocation(portfolio_snapshots)

        # Метрики производительности
        performance_metrics = {}
        if include_performance_metrics:
            performance_metrics = self._calculate_performance_metrics(
                portfolio_snapshots,
                total_cost,
                total_value,
                total_realized_pnl,
                total_unrealized_pnl,
            )

        return PortfolioReport(
            report_id=report_id,
            portfolio_id=portfolio_id,
            portfolio_name=portfolio.name,
            start_date=start_date,
            end_date=end_date,
            generated_at=datetime.now(),
            positions=portfolio_snapshots,
            total_value=total_value,
            total_cost=total_cost,
            total_unrealized_pnl=total_unrealized_pnl,
            total_realized_pnl=total_realized_pnl,
            asset_allocation=asset_allocation,
            top_holdings=top_holdings,
            performance_metrics=performance_metrics,
        )

    def generate_transaction_report(
        self,
        portfolio_id: int,
        start_date: date,
        end_date: date,
        transaction_types: Optional[List[TransactionType]] = None,
        securities: Optional[List[str]] = None,
    ) -> TransactionReport:
        """Генерация отчета по транзакциям"""
        portfolio = self.data_manager.get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")

        report_id = str(uuid.uuid4())

        # Получаем транзакции за период
        transactions = self.get_transactions(portfolio_id, start_date, end_date)

        # Фильтрация по типам транзакций
        if transaction_types:
            transactions = [
                tx for tx in transactions if tx.transaction_type in transaction_types
            ]

        # Фильтрация по ценным бумагам
        if securities:
            transactions = [tx for tx in transactions if tx.secid in securities]

        # Создание сводки по ценным бумагам
        summary_by_security = self._create_transaction_summary(transactions)

        # Общие показатели
        total_buy_amount = sum(
            tx.total_amount
            for tx in transactions
            if tx.transaction_type == TransactionType.BUY
        )
        total_sell_amount = sum(
            tx.total_amount
            for tx in transactions
            if tx.transaction_type == TransactionType.SELL
        )
        total_commission = sum(tx.commission or Decimal("0") for tx in transactions)
        net_cash_flow = total_sell_amount - total_buy_amount - total_commission

        return TransactionReport(
            report_id=report_id,
            portfolio_id=portfolio_id,
            portfolio_name=portfolio.name,
            start_date=start_date,
            end_date=end_date,
            generated_at=datetime.now(),
            transactions=transactions,
            summary_by_security=summary_by_security,
            total_transactions=len(transactions),
            total_buy_amount=total_buy_amount,
            total_sell_amount=total_sell_amount,
            total_commission=total_commission,
            net_cash_flow=net_cash_flow,
        )

    def generate_pnl_report(
        self,
        portfolio_id: int,
        start_date: date,
        end_date: date,
        include_unrealized: bool = True,
        include_dividends: bool = True,
    ) -> PnLReport:
        """Генерация отчета P&L"""
        portfolio = self.data_manager.get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")

        report_id = str(uuid.uuid4())

        # Получаем позиции и транзакции
        positions = self.data_manager.get_positions_for_portfolio(portfolio_id)
        transactions = self.get_transactions(portfolio_id, start_date, end_date)

        pnl_entries = []
        total_realized_pnl = Decimal("0")
        total_unrealized_pnl = Decimal("0")
        total_dividend_income = Decimal("0")

        # Группируем по ценным бумагам
        securities_data = defaultdict(
            lambda: {
                "position": None,
                "transactions": [],
                "realized_pnl": Decimal("0"),
                "dividend_income": Decimal("0"),
            }
        )

        # Добавляем позиции
        for position in positions:
            securities_data[position.secid]["position"] = position

        # Добавляем транзакции
        for tx in transactions:
            securities_data[tx.secid]["transactions"].append(tx)

            if tx.transaction_type == TransactionType.DIVIDEND:
                securities_data[tx.secid]["dividend_income"] += tx.total_amount
            elif tx.transaction_type in [TransactionType.BUY, TransactionType.SELL]:
                # Простой расчет реализованной прибыли (без учета FIFO/LIFO)
                if tx.transaction_type == TransactionType.SELL:
                    # Для продажи считаем прибыль как разность между ценой продажи и средней ценой
                    avg_cost = (
                        securities_data[tx.secid]["position"].avg_price
                        if securities_data[tx.secid]["position"]
                        else tx.price
                    )
                    realized_gain = (tx.price - avg_cost) * tx.quantity
                    securities_data[tx.secid]["realized_pnl"] += realized_gain

        # Создаем записи P&L
        for secid, data in securities_data.items():
            security = self.data_manager.get_security(secid)
            security_name = security.name if security else secid

            realized_pnl = data["realized_pnl"]
            dividend_income = data["dividend_income"]

            # Нереализованная прибыль
            unrealized_pnl = Decimal("0")
            current_price = None
            quantity_held = Decimal("0")
            avg_cost = Decimal("0")

            if data["position"]:
                position = data["position"]
                quantity_held = position.quantity
                avg_cost = position.avg_price

                if include_unrealized:
                    latest_quote = self.data_manager.get_latest_quote(secid)
                    if latest_quote:
                        current_price = latest_quote.price
                        market_value = quantity_held * current_price
                        cost_basis = quantity_held * avg_cost
                        unrealized_pnl = market_value - cost_basis

            total_pnl = realized_pnl + unrealized_pnl

            if realized_pnl != 0 or unrealized_pnl != 0 or dividend_income != 0:
                pnl_entry = PnLEntry(
                    secid=secid,
                    security_name=security_name,
                    realized_pnl=realized_pnl,
                    unrealized_pnl=unrealized_pnl,
                    total_pnl=total_pnl,
                    quantity_held=quantity_held,
                    avg_cost=avg_cost,
                    current_price=current_price,
                    dividend_income=dividend_income,
                )
                pnl_entries.append(pnl_entry)

                total_realized_pnl += realized_pnl
                total_unrealized_pnl += unrealized_pnl
                total_dividend_income += dividend_income

        # Лучшие и худшие исполнители
        best_performers = sorted(pnl_entries, key=lambda x: x.total_pnl, reverse=True)[
            :5
        ]
        worst_performers = sorted(pnl_entries, key=lambda x: x.total_pnl)[:5]

        # Метрики производительности
        total_pnl = total_realized_pnl + total_unrealized_pnl
        performance_metrics = {
            "total_return": total_pnl + total_dividend_income,
            "best_performer": best_performers[0].secid if best_performers else None,
            "worst_performer": worst_performers[0].secid if worst_performers else None,
            "win_rate": (
                len([e for e in pnl_entries if e.total_pnl > 0]) / len(pnl_entries)
                if pnl_entries
                else 0
            ),
        }

        return PnLReport(
            report_id=report_id,
            portfolio_id=portfolio_id,
            portfolio_name=portfolio.name,
            start_date=start_date,
            end_date=end_date,
            generated_at=datetime.now(),
            pnl_entries=pnl_entries,
            total_realized_pnl=total_realized_pnl,
            total_unrealized_pnl=total_unrealized_pnl,
            total_pnl=total_pnl,
            total_dividend_income=total_dividend_income,
            best_performers=best_performers,
            worst_performers=worst_performers,
            performance_metrics=performance_metrics,
        )

    def _calculate_realized_pnl(
        self, portfolio_id: int, start_date: date, end_date: date
    ) -> Decimal:
        """Расчет реализованной прибыли за период"""
        transactions = self.get_transactions(portfolio_id, start_date, end_date)
        realized_pnl = Decimal("0")

        for tx in transactions:
            if tx.transaction_type == TransactionType.SELL:
                # Простой расчет - нужно будет улучшить с учетом FIFO/LIFO
                realized_pnl += tx.total_amount
            elif tx.transaction_type == TransactionType.BUY:
                realized_pnl -= tx.total_amount

        return realized_pnl

    def _create_transaction_summary(
        self, transactions: List[Transaction]
    ) -> List[TransactionSummary]:
        """Создание сводки по транзакциям"""
        summary_data = defaultdict(
            lambda: {
                "security_name": "",
                "buy_quantity": Decimal("0"),
                "sell_quantity": Decimal("0"),
                "buy_amount": Decimal("0"),
                "sell_amount": Decimal("0"),
                "commission": Decimal("0"),
                "count": 0,
            }
        )

        for tx in transactions:
            data = summary_data[tx.secid]
            data["count"] += 1
            data["commission"] += tx.commission or Decimal("0")

            security = self.data_manager.get_security(tx.secid)
            if security and not data["security_name"]:
                data["security_name"] = security.name

            if tx.transaction_type == TransactionType.BUY:
                data["buy_quantity"] += tx.quantity
                data["buy_amount"] += tx.total_amount
            elif tx.transaction_type == TransactionType.SELL:
                data["sell_quantity"] += tx.quantity
                data["sell_amount"] += tx.total_amount

        summaries = []
        for secid, data in summary_data.items():
            summary = TransactionSummary(
                secid=secid,
                security_name=data["security_name"] or secid,
                total_buy_quantity=data["buy_quantity"],
                total_sell_quantity=data["sell_quantity"],
                total_buy_amount=data["buy_amount"],
                total_sell_amount=data["sell_amount"],
                net_quantity=data["buy_quantity"] - data["sell_quantity"],
                total_commission=data["commission"],
                transaction_count=data["count"],
            )
            summaries.append(summary)

        return summaries

    def _calculate_asset_allocation(
        self, snapshots: List[PortfolioSnapshot]
    ) -> Dict[str, Decimal]:
        """Расчет распределения активов (простая группировка)"""
        allocation = defaultdict(Decimal)

        for snapshot in snapshots:
            if snapshot.market_value:
                # Простая группировка по первой букве
                category = snapshot.secid[0] if snapshot.secid else "OTHER"
                allocation[category] += snapshot.market_value

        return dict(allocation)

    def _calculate_performance_metrics(
        self,
        snapshots: List[PortfolioSnapshot],
        total_cost: Decimal,
        total_value: Decimal,
        total_realized_pnl: Decimal,
        total_unrealized_pnl: Decimal,
    ) -> Dict[str, Any]:
        """Расчет метрик производительности"""
        metrics = {}

        if total_cost > 0:
            metrics["total_return_percent"] = (
                (total_value - total_cost) / total_cost * 100
            ).quantize(Decimal("0.01"))
        else:
            metrics["total_return_percent"] = Decimal("0")

        metrics["position_count"] = len(snapshots)
        metrics["profitable_positions"] = len(
            [s for s in snapshots if s.unrealized_pnl and s.unrealized_pnl > 0]
        )
        metrics["total_pnl"] = total_realized_pnl + total_unrealized_pnl

        return metrics
