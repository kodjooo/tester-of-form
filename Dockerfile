# Используем официальный базовый образ Playwright с предустановленными браузерами
FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy

WORKDIR /app

# Устанавливаем зависимости Python
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . .

# Значения по умолчанию для логов и headless
ENV LOG_DIR=/app/logs
ENV HEADLESS=true

# Создаём директорию логов на всякий случай
RUN mkdir -p /app/logs

# Точка входа
CMD ["python", "-m", "app.run"]
