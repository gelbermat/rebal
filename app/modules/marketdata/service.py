from typing import List, Optional
from datetime import datetime
from decimal import Decimal

import aiomoex
import aiohttp

from app.config import settings
from app.logging_config import get_logger
from app.modules.marketdata.models import Security, Quote
from app.storage import DataManager
from app.modules.marketdata.schemas import SecurityCreate, QuoteCreate


logger = get_logger("marketdata.service")


class MOEXAdapter:
    """Адаптер для работы с MOEX API через библиотеку aiomoex"""

    def __init__(self):
        self.session = None

    async def _get_session(self):
        """Получение или создание aiohttp сессии"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def get_securities(
        self, engine: str = "stock", market: str = "shares"
    ) -> List[dict]:
        """Получение списка ценных бумаг с MOEX"""
        try:
            session = await self._get_session()

            securities = await aiomoex.get_board_securities(
                session=session, engine=engine, market=market
            )

            result = []
            for sec in securities:
                result.append(
                    {
                        "secid": sec.get("SECID", ""),
                        "shortname": sec.get("SHORTNAME", ""),
                        "isin": sec.get("ISIN", ""),
                        "boardid": sec.get("BOARDID", ""),
                        "decimals": sec.get("DECIMALS", 0),
                        "lotsize": sec.get("LOTSIZE", 1),
                        "facevalue": sec.get("FACEVALUE", 0),
                        "secname": sec.get("SECNAME", ""),
                        "remarks": sec.get("REMARKS", ""),
                        "marketcode": sec.get("MARKETCODE", ""),
                        "instrid": sec.get("INSTRID", ""),
                        "sectorid": sec.get("SECTORID", ""),
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Error fetching securities from MOEX: {e}")
            return []

    async def get_quotes(
        self,
        secid: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        interval: str = "daily",
    ) -> List[dict]:
        """Получение котировок (свечей) для ценной бумаги"""
        try:
            session = await self._get_session()

            candles = await aiomoex.get_market_candles(
                session=session,
                security=secid,
                start=from_date.strftime("%Y-%m-%d") if from_date else None,
                end=to_date.strftime("%Y-%m-%d") if to_date else None,
                interval=1 if interval == "daily" else 60,  # 1 = дневные, 60 = часовые
            )

            result = []
            for candle in candles:
                result.append(
                    [
                        candle.get("begin", ""),
                        candle.get("open", 0),
                        candle.get("close", 0),
                        candle.get("high", 0),
                        candle.get("low", 0),
                        candle.get("value", 0),
                        candle.get("volume", 0),
                    ]
                )

            return result

        except Exception as e:
            logger.error(f"Error fetching quotes for {secid}: {e}")
            return []

    async def get_current_quotes(self, securities: List[str]) -> List[dict]:
        """Получение текущих котировок для списка ценных бумаг"""
        try:
            session = await self._get_session()

            quotes = await aiomoex.get_market_quotes(
                session=session, securities=securities
            )

            result = []
            for quote in quotes:
                result.append(
                    {
                        "secid": quote.get("SECID", ""),
                        "price": quote.get("LAST", 0),
                        "bid": quote.get("BID", 0),
                        "ask": quote.get("OFFER", 0),
                        "volume": quote.get("VOLTODAY", 0),
                        "change": quote.get("CHANGE", 0),
                        "change_percent": quote.get("CHANGEPRCNT", 0),
                        "timestamp": quote.get("UPDATETIME", ""),
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Error fetching current quotes: {e}")
            return []

    async def get_security_info(self, secid: str) -> Optional[dict]:
        """Получение подробной информации о ценной бумаге"""
        try:
            session = await self._get_session()

            info = await aiomoex.get_security_info(session=session, security=secid)

            if info:
                return {
                    "secid": info.get("SECID", ""),
                    "name": info.get("NAME", ""),
                    "shortname": info.get("SHORTNAME", ""),
                    "isin": info.get("ISIN", ""),
                    "regnumber": info.get("REGNUMBER", ""),
                    "issuesize": info.get("ISSUESIZE", 0),
                    "facevalue": info.get("FACEVALUE", 0),
                    "faceunit": info.get("FACEUNIT", ""),
                    "issuedate": info.get("ISSUEDATE", ""),
                    "matdate": info.get("MATDATE", ""),
                    "typename": info.get("TYPENAME", ""),
                    "group": info.get("GROUP", ""),
                    "type": info.get("TYPE", ""),
                    "groupname": info.get("GROUPNAME", ""),
                    "emitter_id": info.get("EMITTER_ID", ""),
                }

            return None

        except Exception as e:
            logger.error(f"Error fetching security info for {secid}: {e}")
            return None

    async def close(self):
        """Закрытие HTTP сессии"""
        if self.session and not self.session.closed:
            await self.session.close()


class MarketDataService:

    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.moex_adapter = MOEXAdapter()

    async def get_securities(self, skip: int = 0, limit: int = 100) -> List[Security]:
        """Получение ценных бумаг из локального хранилища"""
        securities = self.data_manager.get_all_securities()
        return securities[skip : skip + limit]

    async def create_security(self, security_data: SecurityCreate) -> Security:
        """Создание новой ценной бумаги в локальном хранилище"""
        security = Security(
            secid=security_data.secid,
            name=security_data.name,
            isin=security_data.isin,
            engine=security_data.engine,
            market=security_data.market,
            board=security_data.board,
        )
        self.data_manager.add_security(security)
        return security

    async def sync_securities_from_moex(
        self, engine: str = "stock", market: str = "shares"
    ) -> int:
        """Синхронизация ценных бумаг с MOEX"""
        securities_data = await self.moex_adapter.get_securities(
            engine=engine, market=market
        )
        count = 0

        for sec_data in securities_data:
            if isinstance(sec_data, dict):
                secid = sec_data.get("secid", "")
                name = sec_data.get("shortname", "") or sec_data.get("secname", "")
                isin = sec_data.get("isin", None)
                board = sec_data.get("boardid", None)

                if secid and name and not self.data_manager.security_exists(secid):
                    security = Security(
                        secid=secid,
                        name=name,
                        isin=isin,
                        engine=engine,
                        market=market,
                        board=board,
                    )
                    self.data_manager.add_security(security)
                    count += 1

        return count

    async def get_security_info(self, secid: str) -> Optional[dict]:
        """Получение подробной информации о ценной бумаге с MOEX"""
        return await self.moex_adapter.get_security_info(secid)

    async def sync_quotes_for_security(
        self,
        secid: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> int:
        """Синхронизация котировок для конкретной ценной бумаги"""
        quotes_data = await self.moex_adapter.get_quotes(secid, from_date, to_date)
        count = 0

        for quote_data in quotes_data:
            if len(quote_data) >= 3:
                try:
                    timestamp_str = quote_data[0]
                    open_price = (
                        Decimal(str(quote_data[1])) if quote_data[1] else Decimal("0")
                    )
                    close_price = (
                        Decimal(str(quote_data[2])) if quote_data[2] else Decimal("0")
                    )
                    high_price = (
                        Decimal(str(quote_data[3]))
                        if len(quote_data) > 3 and quote_data[3]
                        else Decimal("0")
                    )
                    low_price = (
                        Decimal(str(quote_data[4]))
                        if len(quote_data) > 4 and quote_data[4]
                        else Decimal("0")
                    )
                    volume = (
                        Decimal(str(quote_data[6]))
                        if len(quote_data) > 6 and quote_data[6]
                        else Decimal("0")
                    )

                    timestamp = (
                        datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                        if timestamp_str
                        else datetime.now()
                    )

                    quote = Quote(
                        secid=secid,
                        timestamp=timestamp,
                        price=close_price,
                        volume=volume,
                        bid=low_price,
                        ask=high_price,
                    )

                    self.data_manager.add_quote(quote)
                    count += 1

                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing quote data for {secid}: {e}")
                    continue

        return count

    async def get_current_quotes(self, securities: List[str]) -> List[dict]:
        """Получение текущих котировок с MOEX"""
        return await self.moex_adapter.get_current_quotes(securities)

    async def update_current_prices(self, securities: List[str]) -> int:
        """Обновление текущих цен для списка ценных бумаг"""
        current_quotes = await self.get_current_quotes(securities)
        count = 0

        for quote_data in current_quotes:
            try:
                secid = quote_data.get("secid")
                price = quote_data.get("price", 0)
                bid = quote_data.get("bid", 0)
                ask = quote_data.get("ask", 0)
                volume = quote_data.get("volume", 0)
                timestamp_str = quote_data.get("timestamp", "")

                if secid and price:
                    if timestamp_str:
                        try:
                            timestamp = datetime.strptime(timestamp_str, "%H:%M:%S")
                            timestamp = timestamp.replace(
                                year=datetime.now().year,
                                month=datetime.now().month,
                                day=datetime.now().day,
                            )
                        except ValueError:
                            timestamp = datetime.now()
                    else:
                        timestamp = datetime.now()

                    quote = Quote(
                        secid=secid,
                        timestamp=timestamp,
                        price=Decimal(str(price)),
                        volume=Decimal(str(volume)) if volume else None,
                        bid=Decimal(str(bid)) if bid else None,
                        ask=Decimal(str(ask)) if ask else None,
                    )

                    self.data_manager.add_quote(quote)
                    count += 1

            except (ValueError, TypeError) as e:
                logger.warning(f"Error processing current quote: {e}")
                continue

        return count

    async def get_latest_quote(self, secid: str) -> Optional[Quote]:
        """Получение последней котировки из локального хранилища"""
        return self.data_manager.get_latest_quote(secid)

    async def get_quotes_history(self, secid: str) -> List[Quote]:
        """Получение истории котировок из локального хранилища"""
        return self.data_manager.get_quotes(secid)

    async def close(self):
        """Закрытие соединений с MOEX"""
        await self.moex_adapter.close()
