import pytest
from decimal import Decimal
from datetime import datetime

from app.modules.strategy.models import StrategyType, StrategyConfig, RebalanceAction
from app.modules.strategy.strategies import LazyIndexTrackingStrategy
from app.modules.portfolio.models import Portfolio, Position


class TestLazyIndexTrackingStrategy:
    """Тесты для стратегии ленивого отслеживания IMOEX"""

    def test_strategy_initialization(self):
        """Тест инициализации стратегии с весами IMOEX"""
        config = StrategyConfig(
            strategy_type=StrategyType.LAZY_INDEX_TRACKING,
            max_weight_deviation=Decimal("0.05"),  # 5% порог для ребалансировки
            min_transaction_amount=Decimal("1000"),
        )

        strategy = LazyIndexTrackingStrategy(config)

        # Проверяем, что стратегия инициализировалась с правильным типом
        assert strategy.strategy_type == StrategyType.LAZY_INDEX_TRACKING
        assert strategy.config.strategy_type == StrategyType.LAZY_INDEX_TRACKING

    def test_imoex_weights_calculation(self):
        """Тест расчета весов IMOEX"""
        config = StrategyConfig(
            strategy_type=StrategyType.LAZY_INDEX_TRACKING,
            max_weight_deviation=Decimal("0.05"),
        )

        strategy = LazyIndexTrackingStrategy(config)

        # Создаем позиции с компонентами IMOEX
        positions = [
            Position(
                id=1,
                portfolio_id=1,
                secid="SBER",
                quantity=Decimal("100"),
                target_weight=None,
                actual_weight=Decimal("0.25"),
                created_at=datetime.now(),
            ),
            Position(
                id=2,
                portfolio_id=1,
                secid="GAZP",
                quantity=Decimal("50"),
                target_weight=None,
                actual_weight=Decimal("0.15"),
                created_at=datetime.now(),
            ),
        ]

        target_weights = strategy.calculate_target_weights(positions)

        # Проверяем, что веса IMOEX правильно рассчитаны
        assert "SBER" in target_weights
        assert "GAZP" in target_weights

        # Проверяем, что сумма весов близка к 1.0
        total_weight = sum(target_weights.values())
        assert abs(total_weight - Decimal("1.0")) < Decimal("0.01")

    def test_imoex_target_weights_for_known_securities(self):
        """Тест целевых весов для известных компонентов IMOEX"""
        config = StrategyConfig(
            strategy_type=StrategyType.LAZY_INDEX_TRACKING,
            max_weight_deviation=Decimal("0.05"),
        )

        strategy = LazyIndexTrackingStrategy(config)

        # Создаем позиции только с основными компонентами IMOEX
        positions = [
            Position(
                id=1,
                portfolio_id=1,
                secid="SBER",
                quantity=Decimal("100"),
                target_weight=None,
                actual_weight=Decimal("0.20"),
                created_at=datetime.now(),
            ),
            Position(
                id=2,
                portfolio_id=1,
                secid="GAZP",
                quantity=Decimal("50"),
                target_weight=None,
                actual_weight=Decimal("0.15"),
                created_at=datetime.now(),
            ),
            Position(
                id=3,
                portfolio_id=1,
                secid="LKOH",
                quantity=Decimal("30"),
                target_weight=None,
                actual_weight=Decimal("0.10"),
                created_at=datetime.now(),
            ),
        ]

        target_weights = strategy.calculate_target_weights(positions)

        # Проверяем, что все известные компоненты имеют целевые веса
        assert len(target_weights) == 3
        assert all(secid in target_weights for secid in ["SBER", "GAZP", "LKOH"])

        # Проверяем относительные пропорции (SBER должен иметь больший вес чем GAZP и LKOH)
        assert target_weights["SBER"] > target_weights["GAZP"]
        assert target_weights["GAZP"] > target_weights["LKOH"]

    def test_rebalancing_with_mock_data(self):
        """Тест ребалансировки с моковыми данными"""
        config = StrategyConfig(
            strategy_type=StrategyType.LAZY_INDEX_TRACKING,
            max_weight_deviation=Decimal("0.05"),
        )

        strategy = LazyIndexTrackingStrategy(config)

        # Создаем позиции с компонентами IMOEX
        positions = [
            Position(
                id=1,
                portfolio_id=1,
                secid="SBER",
                quantity=Decimal("100"),
                target_weight=None,
                actual_weight=Decimal("0.25"),  # 25% - отклонение от целевого
                created_at=datetime.now(),
            ),
            Position(
                id=2,
                portfolio_id=1,
                secid="GAZP",
                quantity=Decimal("50"),
                target_weight=None,
                actual_weight=Decimal("0.05"),  # 5% - отклонение от целевого
                created_at=datetime.now(),
            ),
            Position(
                id=3,
                portfolio_id=1,
                secid="UNKNOWN",  # Не входит в IMOEX
                quantity=Decimal("30"),
                target_weight=None,
                actual_weight=Decimal("0.10"),
                created_at=datetime.now(),
            ),
        ]

        # Рассчитываем целевые веса
        target_weights = strategy.calculate_target_weights(positions)

        # Проверяем, что стратегия корректно обрабатывает известные и неизвестные бумаги
        assert "SBER" in target_weights
        assert "GAZP" in target_weights
        # UNKNOWN должен получить какой-то вес (остаточный после IMOEX компонентов)
        assert "UNKNOWN" in target_weights

        # Проверяем нормализацию весов
        total_weight = sum(target_weights.values())
        assert abs(total_weight - Decimal("1.0")) < Decimal("0.01")

    def test_target_weights_normalization(self):
        """Тест нормализации целевых весов"""
        config = StrategyConfig(
            strategy_type=StrategyType.LAZY_INDEX_TRACKING,
            max_weight_deviation=Decimal("0.05"),  # 5% порог
        )

        strategy = LazyIndexTrackingStrategy(config)

        # Позиции с различными компонентами
        positions = [
            Position(
                id=1,
                portfolio_id=1,
                secid="SBER",
                quantity=Decimal("100"),
                target_weight=None,
                actual_weight=Decimal("0.30"),
                created_at=datetime.now(),
            ),
            Position(
                id=2,
                portfolio_id=1,
                secid="GAZP",
                quantity=Decimal("50"),
                target_weight=None,
                actual_weight=Decimal("0.20"),
                created_at=datetime.now(),
            ),
            Position(
                id=3,
                portfolio_id=1,
                secid="UNKNOWN1",  # Не в IMOEX
                quantity=Decimal("30"),
                target_weight=None,
                actual_weight=Decimal("0.25"),
                created_at=datetime.now(),
            ),
            Position(
                id=4,
                portfolio_id=1,
                secid="UNKNOWN2",  # Не в IMOEX
                quantity=Decimal("20"),
                target_weight=None,
                actual_weight=Decimal("0.25"),
                created_at=datetime.now(),
            ),
        ]

        target_weights = strategy.calculate_target_weights(positions)

        # Проверяем нормализацию - сумма должна быть 1.0
        total_weight = sum(target_weights.values())
        assert abs(total_weight - Decimal("1.0")) < Decimal("0.001")

        # Все позиции должны иметь целевые веса
        assert len(target_weights) == 4
        assert all(
            secid in target_weights
            for secid in ["SBER", "GAZP", "UNKNOWN1", "UNKNOWN2"]
        )

        # SBER и GAZP должны иметь веса согласно IMOEX (пропорционально)
        # UNKNOWN1 и UNKNOWN2 должны получить равные веса из остатка
        assert target_weights["UNKNOWN1"] == target_weights["UNKNOWN2"]


if __name__ == "__main__":
    pytest.main([__file__])
