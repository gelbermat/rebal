"""Настройка логирования на основе конфигурации"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from app.config import settings


def setup_logging() -> logging.Logger:
    """Настройка логирования на основе конфигурации"""

    # Создаем корневой логгер
    logger = logging.getLogger("rebalancer")
    logger.setLevel(getattr(logging, settings.logging.level))

    # Удаляем существующие обработчики
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Создаем форматтер
    formatter = logging.Formatter(settings.logging.format)

    # Настраиваем консольный вывод
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.logging.level))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Настраиваем файловый вывод (если указан путь)
    if settings.logging.file_path:
        log_path = Path(settings.logging.file_path)

        # Создаем директорию для логов, если она не существует
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Используем RotatingFileHandler для ротации логов
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_path,
            maxBytes=settings.logging.max_file_size,
            backupCount=settings.logging.backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, settings.logging.level))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Предотвращаем дублирование сообщений
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """Получение именованного логгера"""
    return logging.getLogger(f"rebalancer.{name}")


# Инициализируем логирование при импорте модуля
setup_logging()
