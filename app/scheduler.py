from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

from app.modules.marketdata.service import MarketDataService
from app.storage import DataManager
from app.logging_config import get_logger
from app.config import settings

logger = get_logger(__name__)


def setup_scheduler(scheduler: AsyncIOScheduler):
    """Настройка планировщика с учетом конфигурации"""

    # Получаем cron выражение в зависимости от режима торгов
    market_data_cron = settings.scheduler.get_market_data_cron()

    logger.info(f"Настройка планировщика в режиме '{settings.scheduler.trading_mode}'")
    logger.info(f"Расписание синхронизации данных: {market_data_cron}")

    scheduler.add_job(
        daily_market_data_update,
        trigger=CronTrigger.from_crontab(
            market_data_cron, timezone=settings.scheduler.timezone
        ),
        id="daily_market_data_update",
        name="Daily Market Data Update",
        replace_existing=True,
    )


async def daily_market_data_update():
    """Ежедневное обновление рыночных данных с MOEX."""
    from datetime import datetime, timedelta

    logger.info(
        f"Starting market data update at {datetime.now()} in {settings.scheduler.trading_mode} mode"
    )

    try:
        data_manager = DataManager()
        market_service = MarketDataService(data_manager)

        securities = await market_service.get_securities()

        if not securities:
            logger.info("No securities found in local storage, loading from MOEX...")
            loaded_count = await market_service.sync_securities_from_moex()
            logger.info(f"Loaded {loaded_count} securities from MOEX")
            securities = await market_service.get_securities()

        if not securities:
            logger.error("Failed to load securities data")
            return

        security_codes = [sec.secid for sec in securities]
        logger.info(f"Processing {len(security_codes)} securities...")

        historical_updated = 0

        for secid in security_codes:
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)

                history_count = await market_service.sync_quotes_for_security(
                    secid=secid, from_date=start_date, to_date=end_date
                )
                historical_updated += history_count
                logger.debug(f"Updated {history_count} historical quotes for {secid}")

            except Exception as e:
                logger.error(f"Failed to update historical data for {secid}: {e}")
                continue

        logger.info(f"Market data update completed successfully:")
        logger.info(f"  - Historical quotes updated: {historical_updated}")
        logger.info(f"  - Securities processed: {len(security_codes)}")

    except Exception as e:
        logger.error(f"Market data update failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        try:
            await market_service.close()
        except:
            pass
