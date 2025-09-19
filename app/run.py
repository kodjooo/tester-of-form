import subprocess
import time
import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Настройка логирования (используем директорию из LOG_DIR)
LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "master.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8"
)

# Расписание: ежедневный запуск в заданное время и часовом поясе
SCHEDULE_DAILY_AT = os.getenv("SCHEDULE_DAILY_AT", "05:00")  # формат HH:MM
SCHEDULE_TZ = os.getenv("SCHEDULE_TZ", "Europe/Moscow")
RUN_ON_START = os.getenv("RUN_ON_START", "false").lower() == "true"


def run_module(module_name: str) -> int:
    """Запуск Python-модуля в подпроцессе и логирование вывода."""
    try:
        logging.info(f"Запуск модуля {module_name}...")
        result = subprocess.run(["python", "-m", module_name], capture_output=True, text=True)
        logging.info(f"Завершение {module_name}. Код: {result.returncode}")
        if result.stdout:
            logging.info(f"{module_name} STDOUT:\n{result.stdout}")
        if result.stderr:
            logging.warning(f"{module_name} STDERR:\n{result.stderr}")
        return result.returncode
    except Exception as exc:
        logging.error(f"Ошибка при запуске {module_name}: {exc}")
        return 1


def run_job_sequence() -> None:
    """Последовательный запуск задач: формы -> ожидание -> проверка почты."""
    code1 = run_module("app.form_tester")
    logging.info("Ожидание 2 минуты перед запуском следующего модуля...")
    time.sleep(120)
    code2 = run_module("app.check_email")
    logging.info(f"Завершена последовательность задач. Коды: form_tester={code1}, check_email={code2}")


def seconds_until_next_run(time_str: str, tz_name: str) -> float:
    """Подсчитать секунды до ближайшего запуска по локальному времени tz_name."""
    tz = ZoneInfo(tz_name)
    now = datetime.now(tz)
    try:
        hour, minute = map(int, time_str.split(":", 1))
    except Exception:
        logging.warning(f"Некорректное время в SCHEDULE_DAILY_AT='{time_str}', используем 05:00")
        hour, minute = 5, 0

    scheduled_today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if scheduled_today <= now:
        scheduled_next = scheduled_today + timedelta(days=1)
    else:
        scheduled_next = scheduled_today

    delta = (scheduled_next - now).total_seconds()
    return max(delta, 0.0)


def main():
    # Одноразовый запуск при старте контейнера (опционально)
    if RUN_ON_START:
        logging.info("RUN_ON_START=true — выполняем задачи немедленно при старте контейнера.")
        run_job_sequence()

    # Основной цикл планировщика (ежедневно)
    while True:
        wait_seconds = seconds_until_next_run(SCHEDULE_DAILY_AT, SCHEDULE_TZ)
        logging.info(
            f"Ожидание {int(wait_seconds)} секунд до следующего запуска в {SCHEDULE_DAILY_AT} ({SCHEDULE_TZ})."
        )
        time.sleep(wait_seconds)
        logging.info("Наступило запланированное время — запускаем задачи.")
        run_job_sequence()


if __name__ == "__main__":
    main()
