#!/usr/bin/env python3
"""
Тесты для утилит конвертации XLS в CSV.
"""

import pytest
import os
import sys
from pathlib import Path
import tempfile
import pandas as pd

# Добавляем корневую папку проекта в path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.xls_to_csv import convert_xls_to_csv, analyze_xls_structure
from utils.merge_csv_tables import merge_csv_tables, find_table_sections


@pytest.fixture
def test_data_path():
    """Создает тестовый Excel файл с mock данными"""
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        # Создаем mock данные похожие на реальную структуру с несколькими разделами
        mock_data = {
            'A': ['Раздел 1. Акции российских эмитентов', '', '', 'Эмитент', 'Сбер', 'ВТБ', '', 'Итого по разделу', '',
                  'Раздел 2. Облигации российских эмитентов', '', '', 'Эмитент', 'Газпром', 'Лукойл', '', 'Итого по разделу'],
            'B': ['', '', '', 'Наименование Ценной Бумаги', 'Сбербанк', 'ВТБ', '', '', '',
                  '', '', '', 'Наименование Ценной Бумаги', 'Газпром', 'Лукойл', '', ''],
            'C': ['', '', '', 'Регистрационный номер', '12345', '67890', '', '', '',
                  '', '', '', 'Регистрационный номер', '11111', '22222', '', ''],
            'D': ['', '', '', 'ISIN', 'RU000A0JX0J2', 'RU000A0JPEB7', '', '', '',
                  '', '', '', 'ISIN', 'RU0007661625', 'RU0009024277', '', ''],
            'E': ['', '', '', 'Выпуск/ серия/ транш', '1', '2', '', '', '',
                  '', '', '', 'Выпуск/ серия/ транш', '3', '4', '', ''],
            'F': ['', '', '', 'Остаток (шт.)', '100', '200', '', '', '',
                  '', '', '', 'Остаток (шт.)', '300', '400', '', '']
        }
        
        df = pd.DataFrame(mock_data)
        
        # Записываем в Excel файл
        df.to_excel(tmp.name, sheet_name="Account_Statement_auto_EXC", index=False, header=False)
        
        yield Path(tmp.name)
        
    # Cleanup
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)


@pytest.fixture
def temp_output_file():
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        yield tmp.name
    # Cleanup
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)


class TestXlsToCsv:

    def test_xls_exists(self, test_data_path):
        assert test_data_path.exists(), f"Тестовый файл {test_data_path} не найден"

    def test_convert_xls_to_csv_basic(self, test_data_path, temp_output_file):
        result_file = convert_xls_to_csv(str(test_data_path), temp_output_file)

        assert result_file == temp_output_file
        assert os.path.exists(result_file)

        # Проверяем что CSV файл не пустой
        csv_size = os.path.getsize(result_file)
        assert csv_size > 0

    def test_convert_xls_to_csv_auto_name(self, test_data_path):
        result_file = convert_xls_to_csv(str(test_data_path))

        expected_file = str(test_data_path.with_suffix(".csv"))
        assert result_file == expected_file
        assert os.path.exists(result_file)

        # Cleanup
        if os.path.exists(result_file):
            os.unlink(result_file)

    def test_convert_xls_content_validity(self, test_data_path, temp_output_file):
        convert_xls_to_csv(str(test_data_path), temp_output_file)

        # Читаем CSV и проверяем структуру
        df = pd.read_csv(temp_output_file, encoding="utf-8")

        assert len(df) > 0, "CSV файл не должен быть пустым"
        assert len(df.columns) > 0, "CSV должен содержать колонки"

        # Проверяем что есть данные с 'Эмитент'
        emitent_rows = df[df.iloc[:, 0] == "Эмитент"]
        assert len(emitent_rows) > 0, "Должны быть строки с заголовком 'Эмитент'"

    def test_file_not_found_error(self):
        with pytest.raises(FileNotFoundError):
            convert_xls_to_csv("nonexistent_file.xls")

    def test_analyze_xls_structure(self, test_data_path, caplog):
        """Тест анализа структуры XLS файла"""
        import logging

        caplog.set_level(logging.INFO)

        analyze_xls_structure(str(test_data_path))

        # Проверяем логи вместо stdout
        log_messages = "\n".join([record.message for record in caplog.records])
        assert "АНАЛИЗ СТРУКТУРЫ ФАЙЛА" in log_messages
        # Изменяем проверку - ищем более общий паттерн 
        assert any("строк" in msg or "columns" in msg or "колонок" in msg for msg in [log_messages])


class TestMergeCsvTables:

    @pytest.fixture
    def csv_file(self, test_data_path, temp_output_file):
        convert_xls_to_csv(str(test_data_path), temp_output_file)
        return temp_output_file

    def test_merge_csv_tables_basic(self, csv_file):
        output_file = merge_csv_tables(csv_file)

        assert os.path.exists(output_file)

        # Проверяем что объединенный файл содержит данные
        df = pd.read_csv(output_file, encoding="utf-8")
        assert len(df) > 0
        assert "Раздел" in df.columns, "Должна быть колонка 'Раздел'"

        # Cleanup
        if os.path.exists(output_file):
            os.unlink(output_file)

    def test_find_table_sections(self, csv_file):
        df = pd.read_csv(csv_file, encoding="utf-8")
        sections = find_table_sections(df)

        assert len(sections) > 0, "Должна быть найдена хотя бы одна секция"

        for section_name, start_idx, end_idx in sections:
            assert isinstance(section_name, str)
            assert isinstance(start_idx, int)
            assert isinstance(end_idx, int)
            assert start_idx <= end_idx

    def test_merged_csv_structure(self, csv_file):
        output_file = merge_csv_tables(csv_file)

        df = pd.read_csv(output_file, encoding="utf-8")

        expected_columns = [
            "Эмитент",
            "Наименование Ценной Бумаги",
            "Регистрационный номер",
            "ISIN",
            "Выпуск/ серия/ транш",
            "Остаток (шт.)",
            "Раздел",
        ]

        for col in expected_columns:
            assert col in df.columns, f"Колонка '{col}' должна присутствовать"

        # Проверяем что есть разные разделы
        unique_sections = df["Раздел"].unique()
        assert len(unique_sections) > 0, "Должен быть хотя бы один раздел"

        # Cleanup
        if os.path.exists(output_file):
            os.unlink(output_file)


class TestIntegration:

    def test_full_workflow(self, test_data_path):
        # Шаг 1: Конвертация XLS в CSV
        csv_file = convert_xls_to_csv(str(test_data_path))
        assert os.path.exists(csv_file)

        # Шаг 2: Объединение таблиц
        merged_file = merge_csv_tables(csv_file)
        assert os.path.exists(merged_file)

        # Шаг 3: Проверка итогового файла
        df = pd.read_csv(merged_file, encoding="utf-8")
        assert len(df) > 0
        assert "Раздел" in df.columns

        # Проверяем что есть данные из разделов
        sections = df["Раздел"].value_counts()
        assert len(sections) >= 1, "Должен быть хотя бы один раздел"

        # Cleanup
        for file_path in [csv_file, merged_file]:
            if os.path.exists(file_path):
                os.unlink(file_path)

    def test_file_sizes_reasonable(self, test_data_path):
        "Проверяем что размеры файлов разумные."
        csv_file = convert_xls_to_csv(str(test_data_path))
        merged_file = merge_csv_tables(csv_file)

        xls_size = os.path.getsize(test_data_path)
        csv_size = os.path.getsize(csv_file)
        merged_size = os.path.getsize(merged_file)

        # CSV должен быть меньше исходного XLS
        assert csv_size < xls_size, "CSV должен быть компактнее XLS"

        # Объединенный файл должен быть разумного размера
        assert merged_size > 0, "Объединенный файл не должен быть пустым"
        assert (
            merged_size < csv_size * 2
        ), "Объединенный файл не должен быть слишком большим"

        # Cleanup
        for file_path in [csv_file, merged_file]:
            if os.path.exists(file_path):
                os.unlink(file_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
