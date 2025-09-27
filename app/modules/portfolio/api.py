from typing import List

from fastapi import APIRouter, HTTPException, Depends

from app.modules.portfolio.service import PortfolioService
from app.modules.portfolio.schemas import (
    Portfolio,
    PortfolioCreate,
    Position,
    PositionCreate,
    PortfolioSummary,
)
from app.storage import get_data_manager, DataManager

router = APIRouter()


def get_portfolio_service(
    data_manager: DataManager = Depends(get_data_manager),
) -> PortfolioService:
    return PortfolioService(data_manager)


@router.post("/", response_model=Portfolio)
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    service: PortfolioService = Depends(get_portfolio_service),
):
    return await service.create_portfolio(portfolio_data)


@router.get("/", response_model=List[Portfolio])
async def get_portfolios(
    skip: int = 0,
    limit: int = 100,
    service: PortfolioService = Depends(get_portfolio_service),
):
    return await service.get_portfolios(skip=skip, limit=limit)


@router.get("/{portfolio_id}", response_model=Portfolio)
async def get_portfolio(
    portfolio_id: int, service: PortfolioService = Depends(get_portfolio_service)
):
    portfolio = await service.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@router.get("/{portfolio_id}/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    portfolio_id: int, service: PortfolioService = Depends(get_portfolio_service)
):
    summary = await service.get_portfolio_summary(portfolio_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return summary


@router.get("/{portfolio_id}/positions", response_model=List[Position])
async def get_portfolio_positions(
    portfolio_id: int, service: PortfolioService = Depends(get_portfolio_service)
):
    return await service.get_portfolio_positions(portfolio_id)


@router.post("/positions", response_model=Position)
async def create_position(
    position_data: PositionCreate,
    service: PortfolioService = Depends(get_portfolio_service),
):
    return await service.create_position(position_data)
