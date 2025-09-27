#!/usr/bin/env python3

import pandas as pd
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import logging

# Настройка логирования для утилиты
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def find_table_sections(df: pd.DataFrame) -> List[Tuple[str, int, int]]:
    """Находит все секции таблиц в CSV файле."""

    header_pattern = "Эмитент"
    sections = []
    current_section = None
    current_start = None

    for i, row in df.iterrows():
        cell_value = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""

        if cell_value == header_pattern:
            if current_section is not None and current_start is not None:
                sections.append((current_section, current_start, i - 1))

            section_name = "Unknown"

            if i > 0:
                prev_cell = (
                    str(df.iloc[i - 1, 0]) if pd.notna(df.iloc[i - 1, 0]) else ""
                )
                if prev_cell and len(prev_cell.strip()) > 0:
                    section_name = prev_cell.strip()
                    if section_name.startswith('"') and section_name.endswith('"'):
                        section_name = section_name[1:-1]
                else:
                    # Если в предыдущей строке пусто, ищем дальше
                    for j in range(max(0, i - 3), i):
                        prev_cell = (
                            str(df.iloc[j, 0]) if pd.notna(df.iloc[j, 0]) else ""
                        )
                        if (
                            prev_cell
                            and not prev_cell.startswith("Эмитент")
                            and not prev_cell.startswith("Итого")
                            and len(prev_cell.strip()) > 0
                            and prev_cell.strip() != ""
                        ):
                            section_name = prev_cell.strip()
                            if section_name.startswith('"') and section_name.endswith(
                                '"'
                            ):
                                section_name = section_name[1:-1]
                            break

            current_section = section_name
            current_start = i + 1

        elif "Итого по разделу" in cell_value or "Итого по счету" in cell_value:
            if current_section is not None and current_start is not None:
                sections.append((current_section, current_start, i - 1))
                current_section = None
                current_start = None

    # Завершаем последнюю секцию
    if current_section is not None and current_start is not None:
        last_data_row = len(df) - 1
        for j in range(len(df) - 1, current_start - 1, -1):
            row_value = str(df.iloc[j, 0]) if pd.notna(df.iloc[j, 0]) else ""
            if (
                row_value
                and not row_value.startswith("Итого")
                and not row_value.startswith("Дата составления")
                and len(row_value.strip()) > 0
            ):
                last_data_row = j
                break
        sections.append((current_section, current_start, last_data_row))

    return sections


def extract_table_data(
    df: pd.DataFrame, sections: List[Tuple[str, int, int]]
) -> pd.DataFrame:
    """Извлекает данные из всех секций и объединяет в одну таблицу."""

    # хардкод колонки результирующей таблицы
    columns = [
        "Эмитент",
        "Наименование Ценной Бумаги",
        "Регистрационный номер",
        "ISIN",
        "Выпуск/ серия/ транш",
        "Остаток (шт.)",
        "Раздел",
    ]

    all_data = []

    for section_name, start_idx, end_idx in sections:
        logger.debug(
            f"Обрабатываем секцию: {section_name} (строки {start_idx}-{end_idx})"
        )

        # Извлекаем данные секции
        for i in range(start_idx, min(end_idx + 1, len(df))):
            row = df.iloc[i]

            # Пропускаем пустые строки
            if pd.isna(row.iloc[0]) or str(row.iloc[0]).strip() == "":
                continue

            cell_value = str(row.iloc[0])
            if "Итого" in cell_value:
                continue

            row_data = []
            for j in range(6):
                if j < len(row):
                    value = row.iloc[j]
                    if pd.isna(value):
                        row_data.append("")
                    else:
                        clean_value = str(value).strip().strip('"')
                        row_data.append(clean_value)
                else:
                    row_data.append("")

            row_data.append(section_name)
            all_data.append(row_data)

    result_df = pd.DataFrame(all_data, columns=columns)
    return result_df


def analyze_csv_structure(df: pd.DataFrame) -> None:
    """Анализирует структуру CSV файла."""

    logger.info(f"Размер файла: {df.shape[0]} строк, {df.shape[1]} колонок")
    logger.info("\nАнализ структуры:")

    sections = find_table_sections(df)
    logger.info(f"\nНайдено секций: {len(sections)}")

    total_records = 0
    for i, (section_name, start_idx, end_idx) in enumerate(sections, 1):
        count = end_idx - start_idx + 1
        logger.info(
            f"  {i}. {section_name}: строки {start_idx}-{end_idx} ({count} записей)"
        )
        total_records += count

    logger.info(f"\nОбщее количество записей для обработки: {total_records}")


def merge_csv_tables(input_file: str, output_file: str = None) -> str:
    """Основная функция объединения таблиц."""

    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Файл не найден: {input_file}")

    if output_file is None:
        output_file = str(input_path.with_suffix("").with_suffix("")) + "_clean.csv"

    logger.info(f"Читаем файл: {input_file}")
    df = pd.read_csv(input_file, encoding="utf-8")

    analyze_csv_structure(df)

    sections = find_table_sections(df)
    if not sections:
        raise ValueError("Не найдено секций с данными для объединения")

    logger.info("\nОбъединяем таблицы...")
    merged_df = extract_table_data(df, sections)

    logger.info(f"Сохраняем в файл: {output_file}")
    merged_df.to_csv(output_file, encoding="utf-8", index=False)

    logger.info(
        f"\nГотово! Объединено {len(merged_df)} записей из {len(sections)} секций"
    )
    logger.info(f"Результат сохранён в: {output_file}")

    return output_file

    # Статистика по разделам
    if "Раздел" in df.columns:
        logger.info(f"\nРаспределение по разделам:")
        section_counts = df["Раздел"].value_counts()
        for section, count in section_counts.items():
            logger.info(f"  {section}: {count} записей")

    # Статистика по типам ценных бумаг
    if "Наименование Ценной Бумаги" in df.columns:
        logger.info(f"\nТипы ценных бумаг:")
        security_types = df["Наименование Ценной Бумаги"].value_counts().head(10)
        for sec_type, count in security_types.items():
            logger.info(f"  {sec_type}: {count}")

    # Показываем первые несколько записей
    logger.info(f"\nПервые 5 записей:")
    logger.info(df.head().to_string())


def main():
    """Основная функция для работы из командной строки."""

    parser = argparse.ArgumentParser(
        description="Объединение нескольких таблиц в CSV файле в одну",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python merge_csv_tables.py statement_sign.csv
  python merge_csv_tables.py statement_sign.csv merged_data.csv
  python merge_csv_tables.py statement_sign.csv --analyze
        """,
    )

    parser.add_argument("input_file", help="Путь к входному CSV файлу")

    parser.add_argument(
        "output_file", nargs="?", help="Путь к выходному CSV файлу (опционально)"
    )

    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Анализировать результат после объединения",
    )

    args = parser.parse_args()

    try:
        if args.analyze:
            df = pd.read_csv(args.input_file, encoding="utf-8")
            analyze_csv_structure(df)
        else:
            merge_csv_tables(args.input_file, args.output_file)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
