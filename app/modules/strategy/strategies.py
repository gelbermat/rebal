from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Dict, Optional
from datetime import datetime

from .models import (
    RebalanceRecommendation,
    RebalanceResult,
    StrategyType,
    RebalanceAction,
    StrategyConfig,
)
from ..portfolio.models import Portfolio, Position


class BaseStrategy(ABC):
    """Базовый абстрактный класс для всех стратегий ребалансировки"""

    def __init__(self, config: StrategyConfig):
        self.config = config

    @property
    @abstractmethod
    def strategy_type(self) -> StrategyType:
        """Возвращает тип стратегии"""
        pass

    @abstractmethod
    def calculate_target_weights(self, positions: List[Position]) -> Dict[str, Decimal]:
        """Рассчитывает целевые веса для каждой позиции"""
        pass

    def calculate_rebalance(
        self,
        portfolio_id: int,
        positions: List[Position],
        current_prices: Dict[str, Decimal],
    ) -> RebalanceResult:
        """Основной метод расчета ребалансировки"""
        target_weights = self.calculate_target_weights(positions)

        # Рассчитываем текущую общую стоимость портфеля
        total_value = self._calculate_total_value(positions, current_prices)

        recommendations = []
        total_cost = Decimal("0")

        for position in positions:
            secid = position.secid
            current_price = current_prices.get(secid, Decimal("0"))

            if current_price == 0:
                continue

            current_quantity = position.quantity
            current_value = current_quantity * current_price
            current_weight = (
                current_value / total_value if total_value > 0 else Decimal("0")
            )

            target_weight = target_weights.get(secid, Decimal("0"))
            target_value = total_value * target_weight
            target_quantity = (
                target_value / current_price if current_price > 0 else Decimal("0")
            )

            quantity_change = target_quantity - current_quantity

            # Определяем действие на основе изменения количества
            action = self._determine_action(quantity_change)

            # Рассчитываем приоритет
            priority = self._calculate_priority(current_weight, target_weight)

            # Ориентировочная стоимость операции
            estimated_cost = abs(quantity_change) * current_price
            total_cost += estimated_cost

            recommendation = RebalanceRecommendation(
                secid=secid,
                current_quantity=current_quantity,
                current_weight=current_weight,
                target_weight=target_weight,
                target_quantity=target_quantity,
                quantity_change=quantity_change,
                action=action,
                estimated_cost=estimated_cost,
                priority=priority,
            )

            recommendations.append(recommendation)

        # Фильтруем рекомендации по минимальному порогу
        filtered_recommendations = self._filter_recommendations(recommendations)

        return RebalanceResult(
            portfolio_id=portfolio_id,
            strategy_type=self.strategy_type,
            current_total_value=total_value,
            target_total_value=total_value,  # Для большинства стратегий целевая стоимость = текущей
            cash_required=self._calculate_cash_required(filtered_recommendations),
            recommendations=filtered_recommendations,
            total_transactions=len(filtered_recommendations),
            estimated_total_cost=total_cost,
            created_at=datetime.now(),
        )

    def _calculate_total_value(
        self, positions: List[Position], current_prices: Dict[str, Decimal]
    ) -> Decimal:
        """Рассчитывает общую стоимость портфеля"""
        total = Decimal("0")
        for position in positions:
            price = current_prices.get(position.secid, Decimal("0"))
            total += position.quantity * price
        return total

    def _determine_action(self, quantity_change: Decimal) -> RebalanceAction:
        """Определяет действие на основе изменения количества"""
        # Используем min_transaction_amount для определения значимого изменения
        # Предполагаем среднюю цену акции 100 руб для расчета минимального количества
        avg_price = Decimal("100")
        min_quantity_threshold = self.config.min_transaction_amount / avg_price

        if quantity_change > min_quantity_threshold:
            return RebalanceAction.BUY
        elif quantity_change < -min_quantity_threshold:
            return RebalanceAction.SELL
        else:
            return RebalanceAction.HOLD

    def _calculate_priority(
        self, current_weight: Decimal, target_weight: Decimal
    ) -> int:
        """Рассчитывает приоритет операции (1-5, где 1 - самый высокий)"""
        weight_diff = abs(current_weight - target_weight)

        if weight_diff >= Decimal("0.1"):  # 10%
            return 1
        elif weight_diff >= Decimal("0.05"):  # 5%
            return 2
        elif weight_diff >= Decimal("0.02"):  # 2%
            return 3
        elif weight_diff >= Decimal("0.01"):  # 1%
            return 4
        else:
            return 5

    def _filter_recommendations(
        self, recommendations: List[RebalanceRecommendation]
    ) -> List[RebalanceRecommendation]:
        """Фильтрует рекомендации по минимальным порогам"""
        filtered = []

        for rec in recommendations:
            # Проверяем минимальный порог изменения веса
            weight_change = abs(rec.current_weight - rec.target_weight)
            if weight_change >= self.config.max_weight_deviation:
                # Проверяем минимальную стоимость операции
                if rec.estimated_cost >= self.config.min_transaction_amount:
                    filtered.append(rec)

        return filtered

    def _calculate_cash_required(
        self, recommendations: List[RebalanceRecommendation]
    ) -> Decimal:
        """Рассчитывает необходимую наличность для ребалансировки"""
        cash_needed = Decimal("0")

        for rec in recommendations:
            if rec.action == RebalanceAction.BUY:
                cash_needed += rec.estimated_cost
            elif rec.action == RebalanceAction.SELL:
                cash_needed -= rec.estimated_cost

        return max(cash_needed, Decimal("0"))


class LazyIndexTrackingStrategy(BaseStrategy):
    """Стратегия ленивого отслеживания индекса IMOEX"""

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.LAZY_INDEX_TRACKING

    def calculate_target_weights(self, positions: List[Position]) -> Dict[str, Decimal]:
        """Рассчитывает веса на основе состава индекса IMOEX"""
        # Веса основных компонентов индекса IMOEX (приблизительные значения)
        # В реальной реализации эти данные должны получаться из API MOEX
        imoex_weights = {
            "SBER": Decimal("0.141"),  # Сбербанк
            "GAZP": Decimal("0.108"),  # Газпром
            "LKOH": Decimal("0.081"),  # ЛУКОЙЛ
            "YNDX": Decimal("0.073"),  # Яндекс
            "GMKN": Decimal("0.056"),  # ГМК Норильский никель
            "NVTK": Decimal("0.045"),  # Новатэк
            "ROSN": Decimal("0.044"),  # Роснефть
            "TCSG": Decimal("0.041"),  # TCS Group
            "PLZL": Decimal("0.039"),  # Полюс
            "MTSS": Decimal("0.037"),  # МТС
            "MAGN": Decimal("0.032"),  # ММК
            "NLMK": Decimal("0.031"),  # НЛМК
            "RUAL": Decimal("0.027"),  # РУСАЛ
            "CHMF": Decimal("0.026"),  # Северсталь
            "ALRS": Decimal("0.024"),  # АЛРОСА
            "VTBR": Decimal("0.023"),  # ВТБ
            "TATN": Decimal("0.022"),  # Татнефть
            "HYDR": Decimal("0.021"),  # РусГидро
            "SNGS": Decimal("0.018"),  # Сургутнефтегаз
            "MOEX": Decimal("0.017"),  # Московская биржа
        }

        # Получаем веса только для тех бумаг, которые есть в портфеле
        target_weights = {}
        total_available_weight = Decimal("0")

        for position in positions:
            if position.secid in imoex_weights:
                target_weights[position.secid] = imoex_weights[position.secid]
                total_available_weight += imoex_weights[position.secid]

        # Если у нас есть бумаги, которых нет в индексе, распределяем остаток поровну
        remaining_positions = [p for p in positions if p.secid not in imoex_weights]
        if remaining_positions and total_available_weight < Decimal("1"):
            remaining_weight = Decimal("1") - total_available_weight
            equal_share = remaining_weight / Decimal(str(len(remaining_positions)))

            for position in remaining_positions:
                target_weights[position.secid] = equal_share

        # Нормализуем веса, чтобы сумма была равна 1
        total_weight = sum(target_weights.values())
        if total_weight > 0:
            target_weights = {
                secid: weight / total_weight for secid, weight in target_weights.items()
            }

        return target_weights

    def _filter_recommendations(
        self, recommendations: List[RebalanceRecommendation]
    ) -> List[RebalanceRecommendation]:
        """Дополнительная фильтрация для ленивого отслеживания"""
        # Для ленивого отслеживания используем более высокий порог для фильтрации
        # чтобы минимизировать количество транзакций
        lazy_threshold = self.config.rebalance_threshold * Decimal(
            "2"
        )  # Удваиваем порог

        filtered = []
        for rec in recommendations:
            weight_deviation = abs(rec.current_weight - rec.target_weight)
            # Применяем более строгую фильтрацию для ленивого подхода
            if weight_deviation >= lazy_threshold:
                # Также проверяем минимальную стоимость транзакции
                if rec.estimated_cost >= self.config.min_transaction_amount:
                    filtered.append(rec)

        return filtered
