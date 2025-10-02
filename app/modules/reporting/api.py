"""FastAPI endpoints для модуля отчетности"""

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from app.storage import get_data_manager, DataManager
from .service import ReportingService
from .schemas import (
    PortfolioReportRequest,
    TransactionReportRequest,
    PnLReportRequest,
    PortfolioReportResponse,
    TransactionReportResponse,
    PnLReportResponse,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)
from .models import TransactionType


router = APIRouter()


def get_reporting_service(
    data_manager: DataManager = Depends(get_data_manager),
) -> ReportingService:
    """Dependency для получения сервиса отчетности"""
    return ReportingService(data_manager)


@router.post("/transactions", response_model=TransactionResponse)
async def create_transaction(
    transaction_data: TransactionCreate,
    reporting_service: ReportingService = Depends(get_reporting_service),
):
    """Создание новой транзакции"""
    try:
        transaction = reporting_service.create_transaction(
            portfolio_id=transaction_data.portfolio_id,
            secid=transaction_data.secid,
            transaction_type=transaction_data.transaction_type,
            quantity=transaction_data.quantity,
            price=transaction_data.price,
            timestamp=transaction_data.timestamp,
            commission=transaction_data.commission,
            notes=transaction_data.notes,
        )
        return TransactionResponse.model_validate(transaction)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    portfolio_id: Optional[int] = Query(None, description="ID портфеля"),
    start_date: Optional[date] = Query(None, description="Начальная дата"),
    end_date: Optional[date] = Query(None, description="Конечная дата"),
    reporting_service: ReportingService = Depends(get_reporting_service),
):
    """Получение списка транзакций с фильтрацией"""
    try:
        transactions = reporting_service.get_transactions(
            portfolio_id=portfolio_id, start_date=start_date, end_date=end_date
        )
        return [TransactionResponse.model_validate(tx) for tx in transactions]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/portfolio-report", response_model=PortfolioReportResponse)
async def generate_portfolio_report(
    request: PortfolioReportRequest,
    reporting_service: ReportingService = Depends(get_reporting_service),
):
    """Генерация отчета по портфелю"""
    try:
        report = reporting_service.generate_portfolio_report(
            portfolio_id=request.portfolio_id,
            start_date=request.start_date,
            end_date=request.end_date,
            include_performance_metrics=request.include_performance_metrics,
            top_holdings_limit=request.top_holdings_limit,
        )
        return PortfolioReportResponse.model_validate(report)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transaction-report", response_model=TransactionReportResponse)
async def generate_transaction_report(
    request: TransactionReportRequest,
    reporting_service: ReportingService = Depends(get_reporting_service),
):
    """Генерация отчета по транзакциям"""
    try:
        report = reporting_service.generate_transaction_report(
            portfolio_id=request.portfolio_id,
            start_date=request.start_date,
            end_date=request.end_date,
            transaction_types=request.transaction_types,
            securities=request.securities,
        )
        return TransactionReportResponse.model_validate(report)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pnl-report", response_model=PnLReportResponse)
async def generate_pnl_report(
    request: PnLReportRequest,
    reporting_service: ReportingService = Depends(get_reporting_service),
):
    """Генерация отчета P&L"""
    try:
        report = reporting_service.generate_pnl_report(
            portfolio_id=request.portfolio_id,
            start_date=request.start_date,
            end_date=request.end_date,
            include_unrealized=request.include_unrealized,
            include_dividends=request.include_dividends,
        )
        return PnLReportResponse.model_validate(report)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio/{portfolio_id}/performance-summary")
async def get_portfolio_performance_summary(
    portfolio_id: int,
    start_date: date = Query(..., description="Начальная дата"),
    end_date: date = Query(..., description="Конечная дата"),
    reporting_service: ReportingService = Depends(get_reporting_service),
):
    """Получение краткой сводки по производительности портфеля"""
    try:
        # Генерируем полный отчет и возвращаем только метрики
        portfolio_report = reporting_service.generate_portfolio_report(
            portfolio_id=portfolio_id,
            start_date=start_date,
            end_date=end_date,
            include_performance_metrics=True,
        )

        pnl_report = reporting_service.generate_pnl_report(
            portfolio_id=portfolio_id, start_date=start_date, end_date=end_date
        )

        return {
            "portfolio_id": portfolio_id,
            "portfolio_name": portfolio_report.portfolio_name,
            "period": {"start_date": start_date, "end_date": end_date},
            "summary": {
                "total_value": portfolio_report.total_value,
                "total_cost": portfolio_report.total_cost,
                "total_pnl": pnl_report.total_pnl,
                "total_return_percent": portfolio_report.performance_metrics.get(
                    "total_return_percent", 0
                ),
                "position_count": len(portfolio_report.positions),
                "realized_pnl": pnl_report.total_realized_pnl,
                "unrealized_pnl": pnl_report.total_unrealized_pnl,
                "dividend_income": pnl_report.total_dividend_income,
            },
            "top_performers": [
                {
                    "secid": entry.secid,
                    "security_name": entry.security_name,
                    "total_pnl": entry.total_pnl,
                    "pnl_percent": (
                        (
                            entry.total_pnl
                            / (entry.avg_cost * entry.quantity_held)
                            * 100
                        ).quantize(entry.total_pnl.__class__("0.01"))
                        if entry.quantity_held > 0 and entry.avg_cost > 0
                        else 0
                    ),
                }
                for entry in pnl_report.best_performers[:3]
            ],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/transaction-volume")
async def get_transaction_volume_analytics(
    portfolio_id: Optional[int] = Query(None, description="ID портфеля"),
    start_date: date = Query(..., description="Начальная дата"),
    end_date: date = Query(..., description="Конечная дата"),
    reporting_service: ReportingService = Depends(get_reporting_service),
):
    """Аналитика объемов транзакций"""
    try:
        transactions = reporting_service.get_transactions(
            portfolio_id=portfolio_id, start_date=start_date, end_date=end_date
        )

        # Группировка по дням
        daily_volume = {}
        transaction_counts = {}

        for tx in transactions:
            day = tx.timestamp.date()
            if day not in daily_volume:
                daily_volume[day] = {"buy": 0, "sell": 0, "total": 0}
                transaction_counts[day] = {"buy": 0, "sell": 0, "total": 0}

            if tx.transaction_type == TransactionType.BUY:
                daily_volume[day]["buy"] += float(tx.total_amount)
                transaction_counts[day]["buy"] += 1
            elif tx.transaction_type == TransactionType.SELL:
                daily_volume[day]["sell"] += float(tx.total_amount)
                transaction_counts[day]["sell"] += 1

            daily_volume[day]["total"] += float(tx.total_amount)
            transaction_counts[day]["total"] += 1

        return {
            "period": {"start_date": start_date, "end_date": end_date},
            "portfolio_id": portfolio_id,
            "daily_volume": daily_volume,
            "daily_counts": transaction_counts,
            "total_volume": sum(float(tx.total_amount) for tx in transactions),
            "total_transactions": len(transactions),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/json")
async def get_portfolio_report_json(
    portfolio_id: int = Query(..., description="ID портфеля"),
    reporting_service: ReportingService = Depends(get_reporting_service),
):
    """
    Получить JSON-отчёт по текущему состоянию портфеля.
    
    Возвращает:
    - Список активов с количеством, средней ценой, текущей ценой, PnL по каждому
    - Суммарную стоимость портфеля и общий PnL
    - Долю акций и облигаций
    """
    try:
        report = await reporting_service.generate_portfolio_json_report(portfolio_id)
        if not report:
            raise HTTPException(
                status_code=404, 
                detail=f"Portfolio with id {portfolio_id} not found"
            )
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


@router.get("/reports/pdf")
async def generate_portfolio_report_pdf(
    portfolio_id: int = Query(..., description="ID портфеля"),
    reporting_service: ReportingService = Depends(get_reporting_service),
):
    """
    Сгенерировать PDF-отчёт по портфелю и вернуть путь к файлу.
    
    Сохраняет файл в папку /reports с именем вида report_<YYYY-MM-DD>.pdf
    """
    try:
        file_path = await reporting_service.generate_portfolio_pdf_report(portfolio_id)
        if not file_path:
            raise HTTPException(
                status_code=404, 
                detail=f"Portfolio with id {portfolio_id} not found"
            )
        return {"file_path": file_path, "message": "PDF report generated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF report: {str(e)}")
