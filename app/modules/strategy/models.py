from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel


class StrategyType(str, Enum):
    """Типы стратегий ребалансировки"""

    LAZY_INDEX_TRACKING = "lazy_index_tracking"


class RebalanceAction(str, Enum):
    """Типы действий при ребалансировке"""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class RebalanceRecommendation(BaseModel):
    """Рекомендация по ребалансировке для одной позиции"""

    secid: str
    current_quantity: Decimal
    current_weight: Decimal
    target_weight: Decimal
    target_quantity: Decimal
    quantity_change: Decimal
    action: RebalanceAction
    estimated_cost: Optional[Decimal] = None
    priority: int = 1  # 1 = высокий приоритет, 5 = низкий


class RebalanceResult(BaseModel):
    """Результат анализа ребалансировки портфеля"""

    portfolio_id: int
    strategy_type: StrategyType
    current_total_value: Decimal
    target_total_value: Decimal
    cash_required: Decimal
    recommendations: List[RebalanceRecommendation]
    total_transactions: int
    estimated_total_cost: Decimal
    created_at: datetime = datetime.now()


class StrategyConfig(BaseModel):
    """Конфигурация стратегии ребалансировки"""

    strategy_type: StrategyType
    parameters: Dict[str, Any] = {}
    min_transaction_amount: Decimal = Decimal("1000")  # Минимальная сумма транзакции
    max_weight_deviation: Decimal = Decimal("0.05")  # Максимальное отклонение веса (5%)
    rebalance_threshold: Decimal = Decimal(
        "0.02"
    )  # Порог для срабатывания ребалансировки (2%)
    transaction_cost_percent: Decimal = Decimal(
        "0.001"
    )  # Комиссия за транзакцию (0.1%)


class Strategy(BaseModel):
    """Модель стратегии ребалансировки"""

    id: int
    name: str
    description: Optional[str] = None
    strategy_type: StrategyType
    config: StrategyConfig
    is_active: bool = True
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class PortfolioStrategy(BaseModel):
    """Связь портфеля со стратегией"""

    id: int
    portfolio_id: int
    strategy_id: int
    is_active: bool = True
    last_rebalance: Optional[datetime] = None
    next_rebalance: Optional[datetime] = None
    created_at: datetime = datetime.now()
