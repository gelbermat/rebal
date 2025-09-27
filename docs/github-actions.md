# GitHub Actions CI/CD

## Обзор

Проект использует GitHub Actions для автоматизации процессов разработки, тестирования и развертывания.

## Структура пайплайна

### Workflow: CI/CD Pipeline (`.github/workflows/ci.yml`)

Пайплайн состоит из четырех основных этапов:

#### 1. 🎨 **Lint** - Проверка качества кода
- **Black** - Форматирование кода
- **isort** - Сортировка импортов  
- **Flake8** - Статический анализ кода

#### 2. 🧪 **Test** - Тестирование
- Матрица тестирования: Python 3.11, 3.12
- PostgreSQL сервис для интеграционных тестов
- Покрытие кода: минимум 80%
- Отправка отчета в Codecov

#### 3. 🔒 **Security** - Проверка безопасности
- **Safety** - Проверка уязвимых зависимостей
- **Bandit** - Анализ безопасности кода

#### 4. 🐳 **Docker** - Сборка и публикация образов
- Многоплатформенная сборка (linux/amd64, linux/arm64)
- Публикация в GitHub Container Registry
- Кэширование слоев для ускорения сборки

## Триггеры

### Push события
- **main** - Полный пайплайн + Docker push
- **develop** - Полный пайплайн + Docker push
- Другие ветки - Только lint и test

### Pull Request
- Любые PR в **main** - Полный пайплайн (без Docker push)

### Manual
- `workflow_dispatch` - Ручной запуск через GitHub UI

## Переменные окружения

### Автоматические
- `GITHUB_TOKEN` - Токен для доступа к GitHub Container Registry
- `DATABASE_URL` - URL PostgreSQL для тестов

### Секреты (не требуются)
Все необходимые токены предоставляются автоматически через `GITHUB_TOKEN`.

## Кэширование

### Poetry зависимости
- Кэш по хешу `poetry.lock`
- Отдельный кэш для каждой версии Python
- Значительно ускоряет сборку

### Docker слои
- GitHub Actions cache для Docker Buildx
- Переиспользование слоев между сборками

## Docker Registry

### GitHub Container Registry (ghcr.io)
Образы публикуются в `ghcr.io/gelbermats/rebalancer` с тегами:
- `main` - Последняя стабильная версия
- `develop` - Версия для разработки
- `pr-{number}` - Pull request версии
- `main-{sha}` / `develop-{sha}` - Версии по коммиту

### Пример использования
```bash
docker pull ghcr.io/gelbermats/rebalancer:main
docker run -p 8000:8000 ghcr.io/gelbermats/rebalancer:main
```

## Статус сборки

Добавьте бейдж в README:
```markdown
[![CI/CD](https://github.com/gelbermats/rebalancer/actions/workflows/ci.yml/badge.svg)](https://github.com/gelbermats/rebalancer/actions/workflows/ci.yml)
```

## Локальное воспроизведение

### Установка act (опционально)
```bash
# macOS
brew install act

# Linux
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```

### Запуск локально
```bash
# Только lint
act -j lint

# Только тесты
act -j test

# Все этапы (кроме Docker)
act
```

## Мониторинг и уведомления

### GitHub Checks
- Все этапы отображаются как отдельные проверки
- Pull Request блокируются при неудачных тестах

### Артефакты
- Отчеты покрытия загружаются в Codecov
- Docker образы в GitHub Container Registry

## Оптимизация производительности

### Средние времена выполнения
- **Lint**: ~2-3 минуты
- **Test** (каждая версия Python): ~3-5 минут
- **Security**: ~2-3 минуты  
- **Docker**: ~5-10 минут
- **Общее время**: ~12-20 минут

### Советы по ускорению
1. **Кэширование зависимостей** - Уже настроено
2. **Параллельное выполнение** - Lint, Test, Security запускаются параллельно
3. **Условное выполнение Docker** - Только для main/develop
4. **Матричное тестирование** - Параллельные версии Python

## Troubleshooting

### Частые проблемы

#### "Coverage check failed"
```bash
# Локальная проверка покрытия
poetry run pytest --cov=app --cov-report=term-missing
poetry run coverage report --fail-under=80
```

#### "Docker build failed"
- Проверьте Dockerfile синтаксис
- Убедитесь что все файлы доступны (не в .dockerignore)
- Проверьте логи в разделе Actions

#### "Import sorting failed"
```bash
# Исправление локально
poetry run isort app/ tests/ utils/
```

#### "Formatting check failed"
```bash
# Исправление локально
poetry run black app/ tests/ utils/
```

### Полезные команды

```bash
# Проверка всех линтеров локально
make lint

# Запуск тестов с покрытием
make test-cov

# Полная проверка как в CI
make ci

# Сборка Docker образа
make docker-build
```

## Безопасность

### Права доступа
- `GITHUB_TOKEN` имеет права только для чтения репозитория и записи в Container Registry
- Никаких дополнительных секретов не требуется

### Изоляция
- Каждый job выполняется в отдельной виртуальной машине
- Зависимости устанавливаются в изолированные окружения

### Сканирование безопасности
- Safety проверяет известные уязвимости в зависимостях
- Bandit анализирует код на потенциальные проблемы безопасности

## Расширение

### Добавление новых этапов
Отредактируйте `.github/workflows/ci.yml`:

```yaml
  new-job:
    name: New Job
    runs-on: ubuntu-latest
    needs: [lint, test]  # Зависимости
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      # ... ваши шаги
```

### Уведомления
Для добавления уведомлений в Slack/Discord/Email используйте соответствующие Actions из GitHub Marketplace.

### Деплой
Для автоматического деплоя добавьте этап после успешной сборки Docker образа.