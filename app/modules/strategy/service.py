from typing import List, Optional, Dict
from decimal import Decimal
from datetime import datetime

from ...storage import DataManager
from .models import Strategy, PortfolioStrategy, StrategyType, StrategyConfig
from .strategies import BaseStrategy, LazyIndexTrackingStrategy
from ..portfolio.models import Portfolio
from ..marketdata.service import MarketDataService


class StrategyService:
    """Сервис для управления стратегиями ребалансировки"""

    def __init__(
        self, data_manager: DataManager, market_data_service: MarketDataService
    ):
        self.data_manager = data_manager
        self.market_data_service = market_data_service
        self._strategy_registry = {
            StrategyType.LAZY_INDEX_TRACKING: LazyIndexTrackingStrategy,
        }

    # === Управление стратегиями ===

    def create_strategy(
        self,
        name: str,
        strategy_type: StrategyType,
        config: StrategyConfig,
        description: Optional[str] = None,
    ) -> Strategy:
        """Создает новую стратегию"""
        strategy_id = len(self.data_manager.strategies) + 1

        strategy = Strategy(
            id=strategy_id,
            name=name,
            description=description,
            strategy_type=strategy_type,
            config=config,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        self.data_manager.strategies[strategy_id] = strategy
        return strategy

    def get_strategy(self, strategy_id: int) -> Optional[Strategy]:
        """Получает стратегию по ID"""
        return self.data_manager.strategies.get(strategy_id)

    def get_all_strategies(self, active_only: bool = False) -> List[Strategy]:
        """Получает все стратегии"""
        strategies = list(self.data_manager.strategies.values())

        if active_only:
            strategies = [s for s in strategies if s.is_active]

        return strategies

    def update_strategy(
        self,
        strategy_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[StrategyConfig] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[Strategy]:
        """Обновляет стратегию"""
        strategy = self.data_manager.strategies.get(strategy_id)
        if not strategy:
            return None

        if name is not None:
            strategy.name = name
        if description is not None:
            strategy.description = description
        if config is not None:
            strategy.config = config
        if is_active is not None:
            strategy.is_active = is_active

        strategy.updated_at = datetime.now()
        return strategy

    def delete_strategy(self, strategy_id: int) -> bool:
        """Удаляет стратегию"""
        if strategy_id in self.data_manager.strategies:
            # Сначала удаляем все привязки к портфелям
            portfolio_strategies_to_remove = [
                ps_id
                for ps_id, ps in self.data_manager.portfolio_strategies.items()
                if ps.strategy_id == strategy_id
            ]

            for ps_id in portfolio_strategies_to_remove:
                del self.data_manager.portfolio_strategies[ps_id]

            # Затем удаляем саму стратегию
            del self.data_manager.strategies[strategy_id]
            return True

        return False

    # === Привязка стратегий к портфелям ===

    def assign_strategy_to_portfolio(
        self, portfolio_id: int, strategy_id: int
    ) -> Optional[PortfolioStrategy]:
        """Привязывает стратегию к портфелю"""
        # Проверяем существование портфеля и стратегии
        if (
            portfolio_id not in self.data_manager.portfolios
            or strategy_id not in self.data_manager.strategies
        ):
            return None

        # Деактивируем старые привязки для этого портфеля
        for ps in self.data_manager.portfolio_strategies.values():
            if ps.portfolio_id == portfolio_id and ps.is_active:
                ps.is_active = False

        # Создаем новую привязку
        ps_id = len(self.data_manager.portfolio_strategies) + 1
        portfolio_strategy = PortfolioStrategy(
            id=ps_id,
            portfolio_id=portfolio_id,
            strategy_id=strategy_id,
            is_active=True,
            created_at=datetime.now(),
        )

        self.data_manager.portfolio_strategies[ps_id] = portfolio_strategy
        return portfolio_strategy

    def get_portfolio_strategy(self, portfolio_id: int) -> Optional[PortfolioStrategy]:
        """Получает активную стратегию для портфеля"""
        for ps in self.data_manager.portfolio_strategies.values():
            if ps.portfolio_id == portfolio_id and ps.is_active:
                return ps
        return None

    def remove_strategy_from_portfolio(self, portfolio_id: int) -> bool:
        """Удаляет привязку стратегии к портфелю"""
        for ps in self.data_manager.portfolio_strategies.values():
            if ps.portfolio_id == portfolio_id and ps.is_active:
                ps.is_active = False
                return True
        return False

    # === Выполнение ребалансировки ===

    def analyze_portfolio_rebalance(
        self,
        portfolio_id: int,
        strategy_id: Optional[int] = None,
        custom_target_weights: Optional[Dict[str, Decimal]] = None,
    ):
        """Анализирует необходимость ребалансировки портфеля"""
        portfolio = self.data_manager.portfolios.get(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")

        # Получаем позиции для портфеля
        positions = self.data_manager.get_positions_for_portfolio(portfolio_id)
        if not positions:
            raise ValueError(f"No positions found for portfolio {portfolio_id}")

        # Определяем стратегию
        if strategy_id is None:
            portfolio_strategy = self.get_portfolio_strategy(portfolio_id)
            if not portfolio_strategy:
                raise ValueError(
                    f"No active strategy found for portfolio {portfolio_id}"
                )
            strategy_id = portfolio_strategy.strategy_id

        strategy = self.get_strategy(strategy_id)
        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")

        # Создаем экземпляр стратегии
        strategy_instance = self._create_strategy_instance(
            strategy, custom_target_weights
        )

        # Получаем текущие цены
        secids = [position.secid for position in positions]
        current_prices = self.market_data_service.get_current_prices(secids)

        # Выполняем анализ ребалансировки
        result = strategy_instance.calculate_rebalance(
            portfolio_id, positions, current_prices
        )

        return result

    def apply_rebalance_recommendations(
        self, portfolio_id: int, recommendation_ids: List[str], confirm: bool = False
    ) -> bool:
        """Применяет рекомендации по ребалансировке (заглушка)"""
        if not confirm:
            return False

        # В реальной реализации здесь было бы взаимодействие с брокерским API
        # для выполнения торговых операций

        # Обновляем время последней ребалансировки
        portfolio_strategy = self.get_portfolio_strategy(portfolio_id)
        if portfolio_strategy:
            portfolio_strategy.last_rebalance = datetime.now()

        return True

    def _create_strategy_instance(
        self,
        strategy: Strategy,
        custom_target_weights: Optional[Dict[str, Decimal]] = None,
    ) -> BaseStrategy:
        """Создает экземпляр стратегии"""
        strategy_class = self._strategy_registry.get(strategy.strategy_type)
        if not strategy_class:
            raise ValueError(f"Unknown strategy type: {strategy.strategy_type}")

        config = strategy.config

        # Если переданы пользовательские веса, добавляем их в конфигурацию
        if (
            custom_target_weights
            and strategy.strategy_type == StrategyType.TARGET_WEIGHT
        ):
            # Создаем копию конфигурации с пользовательскими весами
            config_dict = config.dict() if hasattr(config, "dict") else vars(config)
            config_dict["target_weights"] = custom_target_weights
            config = StrategyConfig(**config_dict)

        return strategy_class(config)

    # === Статистика и аналитика ===

    def get_strategy_performance(self, strategy_id: int, portfolio_id: int) -> Dict:
        """Получает статистику производительности стратегии (заглушка)"""
        # В реальной реализации здесь был бы анализ исторических данных
        # о ребалансировках и их эффективности

        return {
            "strategy_id": strategy_id,
            "portfolio_id": portfolio_id,
            "total_rebalances": 0,
            "avg_deviation": Decimal("0"),
            "total_transaction_cost": Decimal("0"),
            "performance_improvement": None,
            "last_performance_check": datetime.now(),
        }

    def get_portfolio_rebalance_history(self, portfolio_id: int) -> List[Dict]:
        """Получает историю ребалансировок портфеля (заглушка)"""
        # В реальной реализации здесь был бы доступ к истории операций
        return []

    def schedule_rebalance(self, portfolio_id: int, schedule_time: datetime) -> bool:
        """Планирует автоматическую ребалансировку (заглушка)"""
        portfolio_strategy = self.get_portfolio_strategy(portfolio_id)
        if portfolio_strategy:
            portfolio_strategy.next_rebalance = schedule_time
            return True
        return False
