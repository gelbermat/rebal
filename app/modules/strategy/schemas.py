from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from .models import StrategyType, RebalanceAction, StrategyConfig


class StrategyBase(BaseModel):
    """Базовая схема стратегии"""

    name: str = Field(..., description="Название стратегии")
    description: Optional[str] = Field(None, description="Описание стратегии")
    strategy_type: StrategyType = Field(..., description="Тип стратегии")


class StrategyCreate(StrategyBase):
    """Схема для создания стратегии"""

    config: StrategyConfig = Field(..., description="Конфигурация стратегии")


class StrategyUpdate(BaseModel):
    """Схема для обновления стратегии"""

    name: Optional[str] = Field(None, description="Название стратегии")
    description: Optional[str] = Field(None, description="Описание стратегии")
    config: Optional[StrategyConfig] = Field(None, description="Конфигурация стратегии")
    is_active: Optional[bool] = Field(None, description="Активность стратегии")


class StrategyResponse(StrategyBase):
    """Схема ответа со стратегией"""

    id: int = Field(..., description="ID стратегии")
    config: StrategyConfig = Field(..., description="Конфигурация стратегии")
    is_active: bool = Field(..., description="Активность стратегии")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")

    class Config:
        from_attributes = True


class RebalanceRecommendationResponse(BaseModel):
    """Схема ответа с рекомендацией по ребалансировке"""

    secid: str = Field(..., description="Код ценной бумаги")
    current_quantity: Decimal = Field(..., description="Текущее количество")
    current_weight: Decimal = Field(..., description="Текущий вес в портфеле")
    target_weight: Decimal = Field(..., description="Целевой вес в портфеле")
    target_quantity: Decimal = Field(..., description="Целевое количество")
    quantity_change: Decimal = Field(..., description="Изменение количества")
    action: RebalanceAction = Field(..., description="Рекомендуемое действие")
    estimated_cost: Optional[Decimal] = Field(
        None, description="Ориентировочная стоимость"
    )
    priority: int = Field(..., description="Приоритет операции (1-5)")

    class Config:
        from_attributes = True


class RebalanceResultResponse(BaseModel):
    """Схема ответа с результатом анализа ребалансировки"""

    portfolio_id: int = Field(..., description="ID портфеля")
    strategy_type: StrategyType = Field(..., description="Тип стратегии")
    current_total_value: Decimal = Field(..., description="Текущая общая стоимость")
    target_total_value: Decimal = Field(..., description="Целевая общая стоимость")
    cash_required: Decimal = Field(..., description="Требуемая наличность")
    recommendations: List[RebalanceRecommendationResponse] = Field(
        ..., description="Рекомендации"
    )
    total_transactions: int = Field(..., description="Общее количество транзакций")
    estimated_total_cost: Decimal = Field(
        ..., description="Ориентировочная общая стоимость"
    )
    created_at: datetime = Field(..., description="Дата создания")

    class Config:
        from_attributes = True


class PortfolioStrategyCreate(BaseModel):
    """Схема для привязки стратегии к портфелю"""

    portfolio_id: int = Field(..., description="ID портфеля")
    strategy_id: int = Field(..., description="ID стратегии")


class PortfolioStrategyResponse(BaseModel):
    """Схема ответа с привязкой стратегии к портфелю"""

    id: int = Field(..., description="ID привязки")
    portfolio_id: int = Field(..., description="ID портфеля")
    strategy_id: int = Field(..., description="ID стратегии")
    is_active: bool = Field(..., description="Активность привязки")
    last_rebalance: Optional[datetime] = Field(
        None, description="Последняя ребалансировка"
    )
    next_rebalance: Optional[datetime] = Field(
        None, description="Следующая ребалансировка"
    )
    created_at: datetime = Field(..., description="Дата создания")

    class Config:
        from_attributes = True


class RebalanceRequest(BaseModel):
    """Запрос на анализ ребалансировки"""

    portfolio_id: int = Field(..., description="ID портфеля")
    strategy_id: Optional[int] = Field(
        None, description="ID стратегии (если не указан, используется привязанная)"
    )
    simulate_only: bool = Field(True, description="Только симуляция (без выполнения)")
    target_weights: Optional[Dict[str, Decimal]] = Field(
        None, description="Пользовательские целевые веса"
    )


class ApplyRebalanceRequest(BaseModel):
    """Запрос на применение ребалансировки"""

    portfolio_id: int = Field(..., description="ID портфеля")
    recommendations: List[str] = Field(
        ..., description="Список ID рекомендаций для применения"
    )
    confirm: bool = Field(False, description="Подтверждение выполнения")


class StrategyPerformance(BaseModel):
    """Статистика производительности стратегии"""

    strategy_id: int = Field(..., description="ID стратегии")
    portfolio_id: int = Field(..., description="ID портфеля")
    total_rebalances: int = Field(..., description="Общее количество ребалансировок")
    avg_deviation: Decimal = Field(..., description="Среднее отклонение весов")
    total_transaction_cost: Decimal = Field(
        ..., description="Общая стоимость транзакций"
    )
    performance_improvement: Optional[Decimal] = Field(
        None, description="Улучшение производительности (%)"
    )
    last_performance_check: datetime = Field(
        ..., description="Последняя проверка производительности"
    )
