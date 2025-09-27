# Makefile для проекта Rebalancer
.PHONY: help install test lint format security docker clean dev

# Переменные
PYTHON := poetry run python
PIP := poetry run pip
PYTEST := poetry run pytest
BLACK := poetry run black
ISORT := poetry run isort
FLAKE8 := poetry run flake8
SAFETY := poetry run safety
BANDIT := poetry run bandit

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости
	poetry install
	@echo "✅ Зависимости установлены"

install-dev: ## Установить dev зависимости
	poetry install --with dev
	@echo "✅ Dev зависимости установлены"

test: ## Запустить тесты
	$(PYTEST) tests/ -v

test-cov: ## Запустить тесты с покрытием
	$(PYTEST) --cov=app --cov-report=term-missing --cov-report=html tests/
	@echo "📊 HTML отчет доступен в htmlcov/index.html"

test-fast: ## Быстрые тесты (без медленных интеграционных)
	$(PYTEST) tests/ -m "not slow" -x --tb=short

format: ## Форматировать код
	$(BLACK) app/ tests/ utils/
	$(ISORT) app/ tests/ utils/
	@echo "✅ Код отформатирован"

lint: ## Проверить качество кода
	$(FLAKE8) app/ tests/ utils/
	@echo "✅ Линтинг пройден"

format-check: ## Проверить форматирование без изменений
	$(BLACK) --check app/ tests/ utils/
	$(ISORT) --check-only app/ tests/ utils/

security: ## Проверить безопасность
	$(SAFETY) check
	$(BANDIT) -r app/ -f json
	@echo "✅ Проверки безопасности пройдены"

ci: format lint test-cov security ## Запустить все CI проверки локально

dev: ## Запустить приложение в режиме разработки
	$(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker-build: ## Собрать Docker образ
	docker build -t rebalancer:local .
	@echo "✅ Docker образ собран: rebalancer:local"

docker-run: ## Запустить Docker контейнер
	docker run -d \
		--name rebalancer-dev \
		--env-file .env \
		-p 8000:8000 \
		rebalancer:local
	@echo "✅ Контейнер запущен на http://localhost:8000"

docker-stop: ## Остановить Docker контейнер
	docker stop rebalancer-dev || true
	docker rm rebalancer-dev || true
	@echo "✅ Контейнер остановлен"

docker-logs: ## Показать логи Docker контейнера
	docker logs -f rebalancer-dev

clean: ## Очистить временные файлы
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage .pytest_cache/ dist/ build/
	@echo "✅ Временные файлы удалены"

deps-update: ## Обновить зависимости
	poetry update
	@echo "✅ Зависимости обновлены"

deps-audit: ## Проверить устаревшие зависимости
	poetry show --outdated

pre-commit: ## Установить pre-commit hook
	cp .git/hooks/pre-commit .git/hooks/pre-commit.bak 2>/dev/null || true
	chmod +x .git/hooks/pre-commit
	@echo "✅ Pre-commit hook установлен"

env-example: ## Создать .env из .env.example
	cp .env.example .env
	@echo "✅ Файл .env создан из .env.example"
	@echo "⚠️  Отредактируйте .env под ваши настройки"

.DEFAULT_GOAL := help