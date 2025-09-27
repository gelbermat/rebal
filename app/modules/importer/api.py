from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List

from .service import ImportService
from .schemas import (
    BrokerStatementResponse,
    SecurityPositionResponse,
    ImportStatisticsResponse,
)
from .models import BrokerStatement, SecurityPosition


router = APIRouter(prefix="/import", tags=["import"])


def get_import_service() -> ImportService:
    """Dependency для получения сервиса импорта"""
    return ImportService()


def _convert_position_to_response(
    position: SecurityPosition,
) -> SecurityPositionResponse:
    """Конвертирует модель позиции в ответ API"""
    return SecurityPositionResponse(
        issuer=position.issuer,
        security_type=position.security_type,
        trading_code=position.trading_code,
        isin=position.isin,
        currency=position.currency,
        quantity=position.quantity,
        is_bond=position.is_bond,
        is_stock=position.is_stock,
        is_etf=position.is_etf,
    )


def _convert_statement_to_response(
    statement: BrokerStatement,
) -> BrokerStatementResponse:
    """Конвертирует модель отчета в ответ API"""
    return BrokerStatementResponse(
        account_number=statement.account_number,
        statement_date=statement.statement_date,
        total_positions=statement.total_positions,
        bonds_count=len(statement.bonds),
        stocks_count=len(statement.stocks),
        etfs_count=len(statement.etfs),
        positions=[_convert_position_to_response(pos) for pos in statement.positions],
    )


@router.post("/broker-statement", response_model=BrokerStatementResponse)
async def upload_broker_statement(
    file: UploadFile = File(...),
    import_service: ImportService = Depends(get_import_service),
):
    """
    Загружает и парсит брокерский отчет в формате Excel

    - **file**: Excel файл с брокерским отчетом

    Возвращает:
    - Данные о портфеле с разбивкой по типам ценных бумаг
    """

    # Проверяем тип файла
    if not file.filename or not file.filename.endswith((".xls", ".xlsx")):
        raise HTTPException(
            status_code=400, detail="Поддерживаются только Excel файлы (.xls, .xlsx)"
        )

    try:
        # Читаем содержимое файла
        file_bytes = await file.read()

        # Парсим отчет
        statement = import_service.import_from_bytes(file_bytes, file.filename)

        # Конвертируем в ответ
        return _convert_statement_to_response(statement)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Внутренняя ошибка при обработке файла: {str(e)}"
        )


@router.post("/broker-statement/validate", response_model=dict)
async def validate_broker_statement(
    file: UploadFile = File(...),
    import_service: ImportService = Depends(get_import_service),
):
    """
    Валидирует брокерский отчет без импорта данных

    - **file**: Excel файл с брокерским отчетом

    Возвращает:
    - Статистику валидации файла
    """

    # Проверяем тип файла
    if not file.filename or not file.filename.endswith((".xls", ".xlsx")):
        raise HTTPException(
            status_code=400, detail="Поддерживаются только Excel файлы (.xls, .xlsx)"
        )

    try:
        # Читаем содержимое файла
        file_bytes = await file.read()

        # Парсим отчет
        statement = import_service.import_from_bytes(file_bytes, file.filename)

        # Валидируем
        validation_result = import_service.validate_statement(statement)

        return validation_result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Внутренняя ошибка при валидации файла: {str(e)}"
        )


@router.get("/broker-statement/example", response_model=dict)
async def get_example_format():
    """
    Возвращает описание ожидаемого формата брокерского отчета

    Возвращает:
    - Описание структуры Excel файла
    """

    return {
        "description": "Формат брокерского отчета",
        "required_sheet": "Account_Statement_auto_EXC",
        "structure": {
            "account_info": "Строка 3-4: Информация о счете",
            "bonds_section": {
                "start": "Строка с текстом 'Сведения о ценных бумагах'",
                "headers": "Следующая строка: Эмитент, Наименование ценной бумаги, Идентификационный номер, ISIN, Валюта/номер/серия, Остаток (шт.)",
                "data": "Последующие строки с данными об облигациях",
            },
            "stocks_section": {
                "start": "Строка с текстом 'Сведения о ценных бумагах, Classica'",
                "headers": "Те же заголовки что и для облигаций",
                "data": "Данные об акциях и ETF",
            },
        },
        "columns": [
            {"name": "Эмитент", "description": "Наименование эмитента ценной бумаги"},
            {
                "name": "Наименование ценной бумаги",
                "description": "Тип: акция, облигация, ПИФ",
            },
            {"name": "Идентификационный номер", "description": "Торговый код на бирже"},
            {"name": "ISIN", "description": "Международный идентификационный код"},
            {
                "name": "Валюта/номер/серия",
                "description": "Дополнительная информация (может быть пустой)",
            },
            {
                "name": "Остаток (шт.)",
                "description": "Количество ценных бумаг в штуках",
            },
        ],
    }
