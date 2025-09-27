import pytest
import asyncio
from typing import Generator

from app.storage import DataManager


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def data_manager():
    return DataManager()


@pytest.fixture
def sample_security_data():
    return {
        "secid": "SBER",
        "name": "Сбербанк",
        "isin": "RU0009029540",
        "engine": "stock",
        "market": "shares",
        "board": "TQBR",
    }


@pytest.fixture
def sample_portfolio_data():
    return {
        "name": "Test Portfolio",
        "description": "Portfolio for testing",
        "initial_value": "100000.00",
    }


@pytest.fixture
def sample_position_data():
    return {"secid": "SBER", "quantity": 100, "avg_price": "250.00", "portfolio_id": 1}


@pytest.fixture
def sample_order_data():
    return {
        "secid": "SBER",
        "side": "BUY",
        "quantity": 100,
        "price": "250.00",
        "portfolio_id": 1,
    }


@pytest.fixture
def sample_strategy_data():
    return {
        "name": "Low Activity Rebalancing",
        "description": "Quarterly rebalancing strategy",
        "is_active": True,
        "parameters": {"frequency": "quarterly", "threshold": 0.1},
    }
