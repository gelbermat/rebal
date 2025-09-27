"""
Strategy module для управления стратегиями ребалансировки портфелей.

Этот модуль содержит:
- Модели данных для стратегий (models.py)
- Схемы для API (schemas.py)
- Реализации стратегий ребалансировки (strategies.py)
- Сервис для управления стратегий (service.py)
- API endpoints (api.py)

Поддерживаемые типы стратегий:
- LAZY_INDEX_TRACKING: Ленивое отслеживание индекса IMOEX
"""

from .models import (
    StrategyType,
    RebalanceAction,
    StrategyConfig,
    Strategy,
    PortfolioStrategy,
    RebalanceRecommendation,
    RebalanceResult,
)

from .schemas import (
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    PortfolioStrategyCreate,
    PortfolioStrategyResponse,
    RebalanceRequest,
    RebalanceResultResponse,
    ApplyRebalanceRequest,
    StrategyPerformance,
)

from .strategies import BaseStrategy, LazyIndexTrackingStrategy

from .service import StrategyService
from .api import router

__all__ = [
    # Types
    "StrategyType",
    "RebalanceAction",
    # Models
    "StrategyConfig",
    "Strategy",
    "PortfolioStrategy",
    "RebalanceRecommendation",
    "RebalanceResult",
    # Schemas
    "StrategyCreate",
    "StrategyUpdate",
    "StrategyResponse",
    "PortfolioStrategyCreate",
    "PortfolioStrategyResponse",
    "RebalanceRequest",
    "RebalanceResultResponse",
    "ApplyRebalanceRequest",
    "StrategyPerformance",
    # Strategies
    "BaseStrategy",
    "LazyIndexTrackingStrategy",
    # Service
    "StrategyService",
    # Router
    "router",
]
