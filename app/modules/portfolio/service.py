from typing import List, Optional
from decimal import Decimal

from app.modules.portfolio.models import Portfolio, Position
from app.storage import DataManager
from app.modules.portfolio.schemas import (
    PortfolioCreate,
    PositionCreate,
    PortfolioSummary,
)


class PortfolioService:

    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager

    async def create_portfolio(self, portfolio_data: PortfolioCreate) -> Portfolio:
        portfolio_id = self.data_manager.get_next_portfolio_id()

        portfolio = Portfolio(
            id=portfolio_id,
            name=portfolio_data.name,
            description=portfolio_data.description,
        )
        self.data_manager.add_portfolio(portfolio)
        return portfolio

    async def get_portfolio(self, portfolio_id: int) -> Optional[Portfolio]:
        return self.data_manager.get_portfolio(portfolio_id)

    async def get_portfolios(self, skip: int = 0, limit: int = 100) -> List[Portfolio]:
        portfolios = self.data_manager.get_all_portfolios()
        return portfolios[skip : skip + limit]

    async def get_portfolio_positions(self, portfolio_id: int) -> List[Position]:
        return self.data_manager.get_positions_for_portfolio(portfolio_id)

    async def create_position(self, position_data: PositionCreate) -> Position:
        position_id = self.data_manager.get_next_position_id()

        position = Position(
            id=position_id,
            portfolio_id=position_data.portfolio_id,
            secid=position_data.secid,
            quantity=position_data.quantity,
            target_weight=position_data.target_weight,
        )
        self.data_manager.add_position(position)
        return position

    async def update_position_market_data(
        self, position_id: int, market_price: Decimal
    ):
        position = self.data_manager.get_position(position_id)

        if position:
            position.market_price = market_price
            position.market_value = position.quantity * market_price

            if position.avg_price:
                position.unrealized_pnl = (
                    market_price - position.avg_price
                ) * position.quantity

        return position

    async def get_portfolio_summary(
        self, portfolio_id: int
    ) -> Optional[PortfolioSummary]:
        portfolio = await self.get_portfolio(portfolio_id)
        if not portfolio:
            return None

        positions = await self.get_portfolio_positions(portfolio_id)
        total_unrealized_pnl = Decimal("0")
        for position in positions:
            if position.unrealized_pnl:
                total_unrealized_pnl += position.unrealized_pnl

        return PortfolioSummary(
            portfolio=portfolio,
            positions=positions,
            total_unrealized_pnl=total_unrealized_pnl,
            positions_count=len(positions),
        )
