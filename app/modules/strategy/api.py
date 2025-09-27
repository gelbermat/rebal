from typing import List, Optional, Dict
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Depends

from .schemas import (
    StrategyCreate,
    StrategyResponse,
    PortfolioStrategyCreate,
    PortfolioStrategyResponse,
    RebalanceRequest,
    RebalanceResultResponse,
    ApplyRebalanceRequest,
    StrategyPerformance,
)
from .service import StrategyService
from ...storage import get_data_manager
from ..marketdata.service import MarketDataService


def get_strategy_service() -> StrategyService:
    """Dependency для получения сервиса стратегий"""
    data_manager = get_data_manager()
    market_data_service = MarketDataService(data_manager)
    return StrategyService(data_manager, market_data_service)


router = APIRouter(tags=["strategies"])


@router.post("/", response_model=StrategyResponse)
async def create_strategy(
    strategy_data: StrategyCreate,
    strategy_service: StrategyService = Depends(get_strategy_service),
):
    """Создает новую стратегию"""
    try:
        strategy = strategy_service.create_strategy(
            name=strategy_data.name,
            strategy_type=strategy_data.strategy_type,
            config=strategy_data.config,
            description=strategy_data.description,
        )
        return strategy
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[StrategyResponse])
async def get_strategies(
    active_only: bool = False,
    strategy_service: StrategyService = Depends(get_strategy_service),
):
    """Получает список всех стратегий"""
    strategies = strategy_service.get_all_strategies(active_only=active_only)
    return strategies


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: int, strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Получает стратегию по ID"""
    strategy = strategy_service.get_strategy(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


# === Привязка стратегий к портфелям ===


@router.post("/portfolio-assignments", response_model=PortfolioStrategyResponse)
async def assign_strategy_to_portfolio(
    assignment_data: PortfolioStrategyCreate,
    strategy_service: StrategyService = Depends(get_strategy_service),
):
    """Привязывает стратегию к портфелю"""
    portfolio_strategy = strategy_service.assign_strategy_to_portfolio(
        portfolio_id=assignment_data.portfolio_id,
        strategy_id=assignment_data.strategy_id,
    )

    if not portfolio_strategy:
        raise HTTPException(
            status_code=400,
            detail="Failed to assign strategy to portfolio. Check if portfolio and strategy exist.",
        )

    return portfolio_strategy


@router.get(
    "/portfolio-assignments/{portfolio_id}", response_model=PortfolioStrategyResponse
)
async def get_portfolio_strategy(
    portfolio_id: int, strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Получает активную стратегию для портфеля"""
    portfolio_strategy = strategy_service.get_portfolio_strategy(portfolio_id)
    if not portfolio_strategy:
        raise HTTPException(
            status_code=404, detail="No active strategy found for portfolio"
        )

    return portfolio_strategy


# === Ребалансировка ===


@router.post("/rebalance/analyze", response_model=RebalanceResultResponse)
async def analyze_rebalance(
    request: RebalanceRequest,
    strategy_service: StrategyService = Depends(get_strategy_service),
):
    """Анализирует необходимость ребалансировки портфеля"""
    try:
        result = strategy_service.analyze_portfolio_rebalance(
            portfolio_id=request.portfolio_id,
            strategy_id=request.strategy_id,
            custom_target_weights=request.target_weights,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/rebalance/apply")
async def apply_rebalance(
    request: ApplyRebalanceRequest,
    strategy_service: StrategyService = Depends(get_strategy_service),
):
    """Применяет рекомендации по ребалансировке"""
    try:
        success = strategy_service.apply_rebalance_recommendations(
            portfolio_id=request.portfolio_id,
            recommendation_ids=request.recommendations,
            confirm=request.confirm,
        )

        if success:
            return {"message": "Rebalance applied successfully"}
        else:
            return {"message": "Rebalance not applied - confirmation required"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to apply rebalance: {str(e)}"
        )


# === Аналитика ===


@router.get(
    "/performance/{strategy_id}/{portfolio_id}", response_model=StrategyPerformance
)
async def get_strategy_performance(
    strategy_id: int,
    portfolio_id: int,
    strategy_service: StrategyService = Depends(get_strategy_service),
):
    """Получает статистику производительности стратегии"""
    performance = strategy_service.get_strategy_performance(strategy_id, portfolio_id)
    return performance


@router.get("/history/{portfolio_id}")
async def get_rebalance_history(
    portfolio_id: int, strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Получает историю ребалансировок портфеля"""
    history = strategy_service.get_portfolio_rebalance_history(portfolio_id)
    return {"portfolio_id": portfolio_id, "history": history}


@router.post("/schedule/{portfolio_id}")
async def schedule_rebalance(
    portfolio_id: int,
    schedule_time: str,  # ISO datetime string
    strategy_service: StrategyService = Depends(get_strategy_service),
):
    """Планирует автоматическую ребалансировку"""
    try:
        from datetime import datetime

        schedule_datetime = datetime.fromisoformat(schedule_time.replace("Z", "+00:00"))

        success = strategy_service.schedule_rebalance(portfolio_id, schedule_datetime)
        if success:
            return {"message": f"Rebalance scheduled for {schedule_time}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to schedule rebalance")

    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid datetime format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to schedule rebalance: {str(e)}"
        )
