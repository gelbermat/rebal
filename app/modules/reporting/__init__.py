"""Модуль отчетности и аналитики"""

# Модели будут доступны через прямой импорт при необходимости
__all__ = ["ReportingService"]


# Импорт только при необходимости
def get_models():
    from .models import PortfolioReport, TransactionReport, PnLReport

    return PortfolioReport, TransactionReport, PnLReport


def get_service():
    from .service import ReportingService

    return ReportingService
