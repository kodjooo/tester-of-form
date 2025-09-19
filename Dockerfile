# Используем легкий Python образ
FROM python:3.11-slim

WORKDIR /app

# Отключаем интерактивные диалоги для apt и debconf
ENV DEBIAN_FRONTEND=noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN=true
# Отключаем предупреждения pip о root пользователе
ENV PIP_ROOT_USER_ACTION=ignore

# Устанавливаем системные зависимости для Playwright
RUN apt-get update && apt-get install -y \
    wget \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libgtk-4-1 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Обновляем pip и устанавливаем зависимости Python
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --no-warn-script-location -r requirements.txt

# Устанавливаем браузеры Playwright
RUN playwright install chromium

# Копируем проект
COPY . .

# Значения по умолчанию для логов и headless
ENV LOG_DIR=/app/logs
ENV HEADLESS=true

# Создаём директорию логов на всякий случай
RUN mkdir -p /app/logs

# Точка входа
CMD ["python", "-m", "app.run"]
