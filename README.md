## Tester of Form — автоматизация тестирования веб-форм

Система автоматизированного тестирования форм на веб-сайтах. Контейнер запускает модуль `app.run`, который последовательно выполняет:
1. `app.form_tester` — заполнение и отправка форм через Playwright (Chromium)
2. `app.check_email` — проверка почты на наличие писем от форм + отправка отчёта в Telegram

Логи всех операций сохраняются в каталог `logs`.

### Ежедневный запуск по расписанию
- По умолчанию контейнер ожидает ежедневный запуск в `05:00` по `Europe/Moscow`
- Переменные управления расписанием:
  - `SCHEDULE_DAILY_AT` — время запуска в формате `HH:MM` (например, `05:00`)
  - `SCHEDULE_TZ` — часовой пояс IANA (например, `Europe/Moscow`) 
  - `RUN_ON_START` — `true|false` — выполнить задачи один раз при старте контейнера
- Эти значения заданы в `docker-compose.yml` и могут быть переопределены через `.env`

### Структура проекта
- `app/`
  - `form_tester.py` — заполнение форм через Playwright (тестирует 6 различных форм)
  - `check_email.py` — проверка IMAP почты и отправка отчёта в Telegram
  - `run.py` — главная точка входа, планировщик с поддержкой расписания
- `Dockerfile`, `docker-compose.yml`, `requirements.txt`, `.dockerignore`, `.gitignore`
- `logs/` — директория для логов (автоматически монтируется из контейнера)

### Установка/клонирование из Git
```
# HTTPS
git clone <YOUR_REPO_URL>.git tester-of-form && cd tester-of-form
# или SSH
# git clone git@github.com:<org>/<repo>.git tester-of-form && cd tester-of-form

# создайте .env на основе примера ниже
cp /dev/null .env && printf 'HEADLESS=true
LOG_DIR=/app/logs
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
EMAIL_ACCOUNT=your_mail@example.com
EMAIL_PASSWORD=your_app_password
LOOKBACK_MINUTES=15
DELETE_AFTER_PROCESSING=true
TELEGRAM_TOKEN=1111111111:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
TELEGRAM_CHAT_ID=-1000000000000
' >> .env

# запуск
docker compose up -d --build
```

### Требования
- Docker (Desktop на macOS/Windows или пакет docker на Linux)
- (Опционально) Docker Compose v2

### Переменные окружения (.env)

Все критически важные настройки проекта:

**Обязательные переменные:**
- `EMAIL_ACCOUNT` — адрес email для проверки писем (например, `your_mail@gmail.com`)
- `EMAIL_PASSWORD` — пароль или App Password для почтового ящика
- `TELEGRAM_TOKEN` — токен Telegram-бота (формат: `1111111111:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA`)
- `TELEGRAM_CHAT_ID` — ID чата для отправки отчетов (например, `-1000000000000`)

**Настройки почты:**
- `IMAP_SERVER` — IMAP сервер (по умолчанию: `imap.gmail.com`)
- `IMAP_PORT` — порт IMAP (по умолчанию: `993`)
- `LOOKBACK_MINUTES` — период поиска писем в минутах (по умолчанию: `15`)
- `DELETE_AFTER_PROCESSING` — удалять обработанные письма `true|false` (по умолчанию: `true`)

**Настройки надежности Telegram:**
- `TELEGRAM_MAX_RETRIES` — максимальное количество попыток отправки (по умолчанию: `3`)
- `TELEGRAM_RETRY_DELAY` — начальная задержка между попытками в секундах (по умолчанию: `1.0`)
- `TELEGRAM_TIMEOUT` — таймаут для запросов к Telegram API в секундах (по умолчанию: `30`)

**Настройки браузера:**
- `HEADLESS` — режим без графического интерфейса `true|false` (по умолчанию: `true`)

**Логирование:**
- `LOG_DIR` — директория для логов (по умолчанию: `/app/logs`)

**Расписание (управляется через docker-compose.yml):**
- `SCHEDULE_DAILY_AT` — время ежедневного запуска в формате `HH:MM`
- `SCHEDULE_TZ` — часовой пояс IANA
- `RUN_ON_START` — выполнить задачи сразу при запуске контейнера


## Развертывание и управление

### Локальное развертывание с Docker Compose (рекомендуемый способ)

**⚠️ Важно**: В зависимости от версии Docker используйте правильную команду:
- **Docker Compose v2** (новая): `docker compose` (с пробелом)
- **Docker Compose v1** (старая): `docker-compose` (с дефисом)

**Запуск:**
```bash
# Для новых версий Docker (v2+)
docker compose up -d --build

# Для старых версий Docker (v1)
docker-compose up -d --build

# Просмотр логов в реальном времени
docker compose logs -f tester        # v2
docker-compose logs -f tester        # v1

# Проверка статуса контейнера
docker compose ps                    # v2
docker-compose ps                    # v1
```

**Остановка:**
```bash
# Остановить и удалить контейнер
docker compose down                   # v2
docker-compose down                   # v1

# Остановить контейнер (без удаления)
docker compose stop tester           # v2
docker-compose stop tester           # v1

# Перезапуск после изменения кода (без пересборки)
docker compose restart tester        # v2
docker-compose restart tester        # v1
```

**Управление:**
```bash
# Ручной запуск отдельных модулей для тестирования
docker compose run --rm tester python -m app.form_tester    # v2
docker-compose run --rm tester python -m app.form_tester    # v1
docker compose run --rm tester python -m app.check_email    # v2
docker-compose run --rm tester python -m app.check_email    # v1

# Пересборка образа (после изменений в requirements.txt или Dockerfile)
docker compose build --no-cache tester                      # v2
docker-compose build --no-cache tester                      # v1

# Просмотр логов определенного периода
docker compose logs --since="1h" tester                     # v2
docker-compose logs --since="1h" tester                     # v1
```

### Локальная сборка и запуск без Compose

```bash
# Сборка образа
docker build -t tester-of-form:latest .

# Запуск в фоновом режиме с автоперезапуском
docker run -d --name tester-of-form \
  --restart unless-stopped \
  --env-file .env \
  -e SCHEDULE_DAILY_AT=05:00 \
  -e SCHEDULE_TZ=Europe/Moscow \
  -e RUN_ON_START=false \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/app:/app/app \
  tester-of-form:latest

# Остановка и удаление контейнера
docker stop tester-of-form && docker rm tester-of-form

# Просмотр логов
docker logs -f tester-of-form
```

### Развертывание на удаленном сервере

**С Docker Compose (если установлен):**
```bash
# На сервере
git clone https://github.com/kodjooo/tester-of-form.git && cd tester-of-form

# Создайте файл .env с вашими настройками
nano .env
# Добавьте все обязательные переменные из раздела выше

# Запуск в продакшн режиме
docker compose up -d --build           # v2
docker-compose up -d --build           # v1

# Проверка статуса и логов
docker compose ps                       # v2
docker-compose ps                       # v1
docker compose logs -f tester           # v2
docker-compose logs -f tester           # v1

# Остановка
docker compose down                     # v2
docker-compose down                     # v1
```

**Только с Docker (без Compose):**
```bash
# На сервере
git clone https://github.com/kodjooo/tester-of-form.git && cd tester-of-form

# Создайте файл .env с настройками
nano .env

# Сборка и запуск
docker build -t tester-of-form:latest .
docker run -d --name tester-of-form \
  --restart unless-stopped \
  --env-file .env \
  -e SCHEDULE_DAILY_AT=05:00 \
  -e SCHEDULE_TZ=Europe/Moscow \
  -e RUN_ON_START=false \
  -v $(pwd)/logs:/app/logs \
  tester-of-form:latest

# Управление контейнером
docker ps                              # Проверить статус
docker logs -f tester-of-form         # Просмотр логов
docker stop tester-of-form            # Остановка
docker start tester-of-form           # Запуск остановленного контейнера
docker restart tester-of-form         # Перезапуск
docker rm tester-of-form              # Удаление (после остановки)
```

**Обновление на удаленном сервере:**
```bash
# Остановка текущего контейнера
docker stop tester-of-form

# Обновление кода
git pull origin main

# Пересборка и запуск обновленной версии
docker build -t tester-of-form:latest . && docker rm tester-of-form
docker run -d --name tester-of-form \
  --restart unless-stopped \
  --env-file .env \
  -e SCHEDULE_DAILY_AT=05:00 \
  -e SCHEDULE_TZ=Europe/Moscow \
  -e RUN_ON_START=false \
  -v $(pwd)/logs:/app/logs \
  tester-of-form:latest
```

## Дополнительная информация

### Особенности работы
- **Браузер:** Использует Playwright с предустановленными браузерами Chromium в headless-режиме
- **Формы:** Тестирует 6 различных форм на сайтах metawebart.com и meta-sistem.md
- **Логирование:** Создает отдельные логи для каждого модуля (master.log, forms_test.log, form_checker.log)
- **Почта:** Поддерживает IMAP для Gmail и других провайдеров, с возможностью автоудаления обработанных писем
- **Отчеты:** Автоматическая отправка результатов тестирования в Telegram

### Файловая система
- Логи сохраняются в `./logs/` на хосте и в `/app/logs` внутри контейнера
- Исходный код монтируется как volume для разработки (`./app:/app/app`)
- Конфигурация через переменные окружения в `.env`

### Безопасность
- **Важно:** Не коммитьте файл `.env` в репозиторий
- Используйте App Passwords для Gmail вместо обычных паролей
- Храните токены Telegram и пароли почты в секретном месте
- Рекомендуется использовать отдельную почту для тестирования

### Мониторинг и отладка
```bash
# Просмотр всех логов в реальном времени
tail -f logs/*.log

# Проверка конкретного лога
tail -f logs/forms_test.log

# Просмотр логов контейнера
docker compose logs -f tester --tail=100        # v2
docker-compose logs -f tester --tail=100        # v1
```

### Устранение неполадок
- При ошибках браузера проверьте настройку `HEADLESS=true`
- При проблемах с почтой убедитесь, что используете App Password для Gmail
- Проверьте корректность TELEGRAM_TOKEN и CHAT_ID через отправку тестового сообщения
- При изменении требований (`requirements.txt`) всегда пересобирайте образ
