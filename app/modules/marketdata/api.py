from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query

from app.modules.marketdata.service import MarketDataService
from app.modules.marketdata.schemas import Security, Quote
from app.storage import get_data_manager, DataManager

router = APIRouter()


def get_marketdata_service(
    data_manager: DataManager = Depends(get_data_manager),
) -> MarketDataService:
    return MarketDataService(data_manager)


@router.get("/securities", response_model=List[Security])
async def get_securities(
    skip: int = 0,
    limit: int = 100,
    service: MarketDataService = Depends(get_marketdata_service),
):
    """Получение списка ценных бумаг из локального хранилища"""
    try:
        securities = await service.get_securities(skip=skip, limit=limit)
        return securities
    finally:
        await service.close()


@router.post("/securities/sync")
async def sync_securities(
    engine: str = "stock",
    market: str = "shares",
    service: MarketDataService = Depends(get_marketdata_service),
):
    """Синхронизация ценных бумаг с MOEX"""
    try:
        count = await service.sync_securities_from_moex(engine=engine, market=market)
        return {"message": f"Synchronized {count} securities from MOEX"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.get("/securities/{secid}/info")
async def get_security_info(
    secid: str, service: MarketDataService = Depends(get_marketdata_service)
):
    """Получение подробной информации о ценной бумаге с MOEX"""
    try:
        info = await service.get_security_info(secid)
        if not info:
            raise HTTPException(status_code=404, detail="Security not found")
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.post("/quotes/{secid}/sync")
async def sync_quotes_for_security(
    secid: str,
    from_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    service: MarketDataService = Depends(get_marketdata_service),
):
    """Синхронизация исторических котировок для ценной бумаги"""
    try:
        # Парсим даты
        start_date = None
        end_date = None

        if from_date:
            try:
                start_date = datetime.strptime(from_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid from_date format. Use YYYY-MM-DD"
                )

        if to_date:
            try:
                end_date = datetime.strptime(to_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid to_date format. Use YYYY-MM-DD"
                )

        count = await service.sync_quotes_for_security(secid, start_date, end_date)
        return {"message": f"Synchronized {count} quotes for {secid}"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.post("/quotes/current/update")
async def update_current_prices(
    securities: List[str], service: MarketDataService = Depends(get_marketdata_service)
):
    """Обновление текущих цен для списка ценных бумаг"""
    try:
        count = await service.update_current_prices(securities)
        return {"message": f"Updated current prices for {count} securities"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.get("/quotes/current")
async def get_current_quotes(
    securities: List[str] = Query(..., description="List of security codes"),
    service: MarketDataService = Depends(get_marketdata_service),
):
    """Получение текущих котировок с MOEX"""
    try:
        quotes = await service.get_current_quotes(securities)
        return quotes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.get("/quotes/{secid}/latest", response_model=Quote)
async def get_latest_quote(
    secid: str, service: MarketDataService = Depends(get_marketdata_service)
):
    """Получение последней котировки из локального хранилища"""
    try:
        quote = await service.get_latest_quote(secid)
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        return quote
    finally:
        await service.close()


@router.get("/quotes/{secid}/history", response_model=List[Quote])
async def get_quotes_history(
    secid: str, service: MarketDataService = Depends(get_marketdata_service)
):
    """Получение истории котировок из локального хранилища"""
    try:
        quotes = await service.get_quotes_history(secid)
        return quotes
    finally:
        await service.close()
