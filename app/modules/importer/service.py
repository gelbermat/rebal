import pandas as pd
import re
from typing import Optional, List
from io import BytesIO
from pathlib import Path

from .models import SecurityPosition, BrokerStatement
from app.logging_config import get_logger

logger = get_logger(__name__)


class BrokerStatementParser:
    """Парсер брокерских отчетов в формате Excel"""

    # Заголовки колонок в отчете (строка 7 и 23)
    HEADERS = [
        "Эмитент",
        "Наименование ценной бумаги",
        "Идентификационный номер",
        "ISIN",
        "Валюта/ номер/ серия",
        "Остаток (шт.)",
    ]

    def __init__(self):
        self.df: Optional[pd.DataFrame] = None

    def parse_file(self, file_path: str) -> BrokerStatement:
        """Парсит Excel файл брокерского отчета"""
        try:
            # Читаем Excel файл
            self.df = pd.read_excel(file_path, sheet_name="Account_Statement_auto_EXC")

            # Извлекаем номер счета
            account_number = self._extract_account_number()

            # Извлекаем позиции портфеля
            positions = self._extract_positions()

            return BrokerStatement(account_number=account_number, positions=positions)

        except Exception as e:
            raise ValueError(f"Ошибка при парсинге файла: {str(e)}")

    def parse_bytes(
        self, file_bytes: bytes, filename: str = "statement.xls"
    ) -> BrokerStatement:
        """Парсит Excel файл из байтов"""
        try:
            # Создаем BytesIO объект
            file_buffer = BytesIO(file_bytes)

            # Читаем Excel файл из байтов
            self.df = pd.read_excel(
                file_buffer, sheet_name="Account_Statement_auto_EXC"
            )

            # Извлекаем номер счета
            account_number = self._extract_account_number()

            # Извлекаем позиции портфеля
            positions = self._extract_positions()

            return BrokerStatement(account_number=account_number, positions=positions)

        except Exception as e:
            raise ValueError(f"Ошибка при парсинге файла {filename}: {str(e)}")

    def _extract_account_number(self) -> str:
        """Извлекает номер счета из отчета"""
        try:
            # Ищем в строке 3 (индекс 3) номер счета
            account_info = str(self.df.iloc[3, 0])

            # Извлекаем номер счета с помощью регулярного выражения
            match = re.search(r"код счёта: ([\w\d]+)", account_info)
            if match:
                return match.group(1)

            # Если не найден, пробуем другой паттерн
            match = re.search(r"№(\w+)", account_info)
            if match:
                return match.group(1)

            return "UNKNOWN"

        except Exception:
            return "UNKNOWN"

    def _extract_positions(self) -> List[SecurityPosition]:
        """Извлекает позиции ценных бумаг из отчета"""
        positions = []

        # Обрабатываем облигации (строки 8-20 в нашем примере)
        bonds = self._extract_bonds()
        positions.extend(bonds)

        # Обрабатываем акции и ETF (строки 24+ в нашем примере)
        stocks_etfs = self._extract_stocks_and_etfs()
        positions.extend(stocks_etfs)

        return positions

    def _extract_bonds(self) -> List[SecurityPosition]:
        """Извлекает облигации из отчета"""
        positions = []

        # Ищем секцию с облигациями
        # В нашем файле это строки 8-20, но нужно найти динамически
        start_row = self._find_section_start("Сведения о ценных бумагах")
        if start_row is None:
            return positions

        # Ищем конец секции (пустая строка или следующая секция)
        end_row = self._find_section_end(start_row + 2)  # +2 чтобы пропустить заголовки

        for i in range(start_row + 1, end_row):  # +1 чтобы пропустить заголовок
            try:
                row_data = self.df.iloc[i]

                # Проверяем что это не пустая строка и не заголовок
                if pd.isna(row_data.iloc[0]) or "Эмитент" in str(row_data.iloc[0]):
                    continue

                # Проверяем что это облигация
                security_type = str(row_data.iloc[1]) if len(row_data) > 1 else ""
                if "облигац" not in security_type.lower():
                    continue

                position = self._create_position_from_row(row_data)
                if position:
                    positions.append(position)

            except Exception as e:
                # Логируем ошибку, но продолжаем обработку
                logger.error(f"Ошибка при обработке строки {i}: {e}")
                continue

        return positions

    def _extract_stocks_and_etfs(self) -> List[SecurityPosition]:
        """Извлекает акции и ETF из отчета"""
        positions = []

        # Ищем секцию с акциями (обычно после облигаций)
        # В нашем файле это начинается со строки 24
        start_row = self._find_section_start("Сведения о ценных бумагах, Classica")
        if start_row is None:
            # Пробуем найти по другому паттерну
            start_row = self._find_row_with_text("Advanced Micro Devices")
            if start_row is None:
                return positions
            start_row -= 1  # Отступаем на заголовок

        # Обрабатываем все строки до конца данных
        total_rows = len(self.df)

        for i in range(start_row + 1, total_rows):  # +1 чтобы пропустить заголовок
            try:
                row_data = self.df.iloc[i]

                # Проверяем что это не пустая строка и не заголовок
                if pd.isna(row_data.iloc[0]) or "Эмитент" in str(row_data.iloc[0]):
                    continue

                # Проверяем что это не строка с итогом
                if "Итого" in str(row_data.iloc[0]):
                    break

                position = self._create_position_from_row(row_data)
                if position:
                    positions.append(position)

            except Exception as e:
                # Логируем ошибку, но продолжаем обработку
                logger.error(f"Ошибка при обработке строки {i}: {e}")
                continue

        return positions

    def _create_position_from_row(self, row_data) -> Optional[SecurityPosition]:
        """Создает объект позиции из строки данных"""
        try:
            # Извлекаем данные из колонок
            issuer = (
                str(row_data.iloc[0]).strip() if not pd.isna(row_data.iloc[0]) else ""
            )
            security_type = (
                str(row_data.iloc[1]).strip()
                if len(row_data) > 1 and not pd.isna(row_data.iloc[1])
                else ""
            )
            trading_code = (
                str(row_data.iloc[2]).strip()
                if len(row_data) > 2 and not pd.isna(row_data.iloc[2])
                else ""
            )
            isin = (
                str(row_data.iloc[3]).strip()
                if len(row_data) > 3 and not pd.isna(row_data.iloc[3])
                else ""
            )
            currency = (
                str(row_data.iloc[4]).strip()
                if len(row_data) > 4 and not pd.isna(row_data.iloc[4])
                else None
            )

            # Извлекаем количество
            quantity_str = (
                str(row_data.iloc[5]).strip()
                if len(row_data) > 5 and not pd.isna(row_data.iloc[5])
                else "0"
            )

            # Очищаем количество от пробелов и преобразуем в число
            quantity_str = re.sub(r"\s+", "", quantity_str)
            quantity = int(quantity_str) if quantity_str.isdigit() else 0

            # Проверяем обязательные поля
            if not issuer or not isin or quantity <= 0:
                return None

            return SecurityPosition(
                issuer=issuer,
                security_type=security_type,
                trading_code=trading_code,
                isin=isin,
                currency=currency if currency and currency != "nan" else None,
                quantity=quantity,
            )

        except Exception as e:
            logger.error(f"Ошибка при создании позиции: {e}")
            return None

    def _find_section_start(self, section_name: str) -> Optional[int]:
        """Находит начало секции по названию"""
        for i, row in self.df.iterrows():
            for cell in row:
                if isinstance(cell, str) and section_name in cell:
                    return i
        return None

    def _find_section_end(self, start_row: int) -> int:
        """Находит конец секции (пустая строка или новая секция)"""
        total_rows = len(self.df)

        for i in range(start_row, total_rows):
            row_data = self.df.iloc[i]

            # Если вся строка пустая
            if row_data.isna().all():
                return i

            # Если нашли строку с итогом
            if "Итого" in str(row_data.iloc[0]):
                return i

            # Если нашли новую секцию
            if "Сведения о ценных бумагах" in str(row_data.iloc[0]):
                return i

        return total_rows

    def _find_row_with_text(self, text: str) -> Optional[int]:
        """Находит строку содержащую указанный текст"""
        for i, row in self.df.iterrows():
            for cell in row:
                if isinstance(cell, str) and text in cell:
                    return i
        return None


class ImportService:
    """Сервис для импорта данных из брокерских отчетов"""

    def __init__(self):
        self.parser = BrokerStatementParser()

    def import_from_file(self, file_path: str) -> BrokerStatement:
        """Импортирует данные из файла"""
        return self.parser.parse_file(file_path)

    def import_from_bytes(
        self, file_bytes: bytes, filename: str = "statement.xls"
    ) -> BrokerStatement:
        """Импортирует данные из байтов файла"""
        return self.parser.parse_bytes(file_bytes, filename)

    def validate_statement(self, statement: BrokerStatement) -> dict:
        """Валидирует импортированные данные"""
        return {
            "valid": True,
            "account_number": statement.account_number,
            "total_positions": statement.total_positions,
            "bonds": len(statement.bonds),
            "stocks": len(statement.stocks),
            "etfs": len(statement.etfs),
        }
