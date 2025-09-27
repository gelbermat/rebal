FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов зависимостей
COPY pyproject.toml poetry.lock* ./

# Установка Poetry
RUN pip install poetry==1.7.1

# Конфигурация Poetry
RUN poetry config virtualenvs.create false

# Установка зависимостей только для production
RUN poetry install --only=main --no-dev

# Копирование кода приложения
COPY app/ ./app/
COPY utils/ ./utils/

# Создание директории для логов
RUN mkdir -p /app/logs

# Создание пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Порт приложения
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Команда запуска
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
