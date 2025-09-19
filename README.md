## Tester of Form — запуск в Docker

Кратко: контейнер запускает модуль `app.run`, который последовательно выполняет `app.form_tester` (Playwright) и `app.check_email` (проверка писем + отправка отчёта в Telegram). Логи пишутся в каталог `logs`.

### Структура проекта
- `app/`
  - `form_tester.py` — отправка форм через Playwright
  - `check_email.py` — проверка почты и отчёт в Telegram
  - `run.py` — точка входа, поочерёдный запуск модулей
- `Dockerfile`, `docker-compose.yml`, `requirements.txt`, `.dockerignore`, `.gitignore`
- `logs/` — директория для логов (монтируется наружу)

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
Содержимое `.env` см. выше (в блоке клонирования). Значимые ключи: `EMAIL_ACCOUNT`, `EMAIL_PASSWORD`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`.

### Локальный запуск (через Docker Compose)
```
docker compose up -d --build
```
- Логи будут в каталоге `./logs` на вашей машине.
- Остановить и удалить контейнер: `docker compose down`

### Режим разработки (без пересборки образа)
- Смонтирован каталог исходников: `./app:/app/app`.
- Правьте код в `app/`, затем:
```
docker compose restart tester
```
- Запуск отдельных модулей:
```
docker compose run --rm tester python -m app.form_tester
docker compose run --rm tester python -m app.check_email
```
- Пересборка нужна только при изменении `requirements.txt`/`Dockerfile`.

### Локальная сборка и запуск без Compose
```
docker build -t tester-of-form:latest .
docker run --rm --name tester-of-form \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/app:/app/app \
  tester-of-form:latest
```

### Запуск на удалённом сервере (установлен только Docker)
```
# на сервере
git clone <YOUR_REPO_URL>.git tester-of-form && cd tester-of-form
# создайте .env и запустите
docker build -t tester-of-form:latest .
docker run --rm --name tester-of-form \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  tester-of-form:latest
```

### Примечания
- Браузеры Playwright уже внутри базового образа, интерфейс выключен (`HEADLESS=true`).
- Логи сохраняются в `./logs` на хосте и в `/app/logs` внутри контейнера.
- Секреты храните в `.env`/секретах CI, не коммитьте их.
- Точка входа: `python -m app.run`.
