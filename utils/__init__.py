"""
Утилиты для работы с брокерскими отчетами.
"""

from .xls_to_csv import convert_xls_to_csv, analyze_xls_structure
from .merge_csv_tables import merge_csv_tables, find_table_sections

__all__ = [
    "convert_xls_to_csv",
    "analyze_xls_structure",
    "merge_csv_tables",
    "find_table_sections",
]
