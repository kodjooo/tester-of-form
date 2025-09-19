import subprocess
import time
import logging
import os

# Настройка логирования (используем директорию из LOG_DIR)
LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "master.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8"
)


def run_module(module_name: str):
    try:
        logging.info(f"Запуск модуля {module_name}...")
        result = subprocess.run(["python", "-m", module_name], capture_output=True, text=True)
        logging.info(f"Завершение {module_name}. Код: {result.returncode}")
        if result.stdout:
            logging.info(f"{module_name} STDOUT:\n{result.stdout}")
        if result.stderr:
            logging.warning(f"{module_name} STDERR:\n{result.stderr}")
    except Exception as e:
        logging.error(f"Ошибка при запуске {module_name}: {e}")


def main():
    run_module("app.form_tester")

    logging.info("Ожидание 2 минуты перед запуском следующего модуля...")
    time.sleep(120)

    run_module("app.check_email")


if __name__ == "__main__":
    main()
