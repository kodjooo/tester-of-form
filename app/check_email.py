import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
import requests
import logging
import os

# === ЛОГИРОВАНИЕ ===
LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "form_checker.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DELETE_AFTER_PROCESSING = os.getenv("DELETE_AFTER_PROCESSING", "true").lower() == "true"  # Управление удалением писем через переменную окружения

# === НАСТРОЙКИ ===
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT", "")  # Должно быть передано через переменные окружения
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")  # Должно быть передано через переменные окружения
LOOKBACK_MINUTES = int(os.getenv("LOOKBACK_MINUTES", "15"))

# === ТЕЛЕГРАМ ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")  # Должно быть передано через переменные окружения
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")  # Должно быть передано через переменные окружения

# === ДАННЫЕ ДЛЯ ПРОВЕРКИ ФОРМ ===
FORMS = {
    "metawebart.com": {
        "Форма 1": [
            "Metawebart.com",
            "mark.aborchie@gmail.com",
            "+35800000000"
        ],
        "Форма 2": [
            "Metawebart.com",
            "+35800000000"
        ],
        "Форма 3": [
            "Metawebart.com",
            "mark.aborchie@gmail.com",
            "+35811111111"
        ],
        "Форма 4": [
            "Metawebart.com",
            "+35811111111"
        ]
    },
    "meta-sistem.md": {
        "Форма 5": [
            "meta-sistem.md",
            "mark.aborchie@gmail.com",
            "+79990000000"
        ],
        "Форма 6": [
            "meta-sistem.md",
            "mark.aborchie@gmail.com",
            "+79990000001",
            "https://meta-test.com/"
        ]
    }
}


def fetch_recent_messages():
    logger.info("🔄 Подключаемся к почтовому ящику и ищем письма...")
    try:
        mailbox = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mailbox.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        mailbox.select("inbox")

        since = (datetime.now() - timedelta(minutes=LOOKBACK_MINUTES)).strftime("%d-%b-%Y")
        status, messages = mailbox.search(None, f'(SINCE "{since}")')

        if status != "OK":
            logger.error("❌ Ошибка при поиске писем")
            mailbox.logout()
            return []

        message_ids = messages[0].split()
        emails = []

        logger.info(f"📩 Найдено писем: {len(message_ids)}")

        for msg_id in reversed(message_ids):
            status, msg_data = mailbox.fetch(msg_id, "(RFC822)")
            if status != "OK":
                logger.warning(f"⚠️ Не удалось получить письмо ID {msg_id}")
                continue

            msg = email.message_from_bytes(msg_data[0][1])
            subject, encoding = decode_header(msg["Subject"])[0]
            msg_date_raw = msg.get("Date")
            msg_date_str = msg_date_raw or "неизвестно"
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8")

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")

            emails.append({
                "msg_id": msg_id,
                "subject": subject,
                "body": body,
                "date": msg_date_str,
                "short_body": body[:100].replace("\n", " ").strip()
            })

        mailbox.logout()
        return emails

    except Exception as e:
        logger.exception("❌ Ошибка при получении писем:")
        return []


def check_forms(emails):
    report = []
    debug_logs = []
    matched_msg_ids = set()

    logger.info("🔍 Начинаем проверку писем на соответствие формам...")

    for site, forms in FORMS.items():
        report.append(f"\nСайт {site}")
        for form_name, conditions in forms.items():
            found = False
            form_debug = f"\n➡️ {form_name}:"

            for email_data in emails:
                msg_date_str = email_data.get("date", "неизвестно")
                short_body = email_data.get("short_body", "")
                subject = email_data["subject"]
                body = email_data["body"]

                matched = []
                missing = []

                for c in conditions:
                    c_lower = c.lower()
                    if c_lower in subject.lower() or c_lower in body.lower():
                        matched.append(c)
                    else:
                        missing.append(c)

                if not missing:
                    found = True
                    matched_msg_ids.add(email_data["msg_id"])
                    form_debug += f"\n✅ Найдено письмо с подходящей темой и телом."
                    break
                else:
                    form_debug += f"\n❌ Письмо: \"{subject.strip()}\""
                    form_debug += f"\n   Получено: {msg_date_str}"
                    form_debug += f"\n   Тело (начало): \"{short_body}\""
                    form_debug += f"\n   - Совпали: {matched}"
                    form_debug += f"\n   - Отсутствуют: {missing}"

            status = "работает" if found else "не работает"
            report.append(f"{form_name} - {status}")
            debug_logs.append(form_debug)

    return "\n".join(report), "\n".join(debug_logs), matched_msg_ids


def delete_emails(msg_ids):
    if not DELETE_AFTER_PROCESSING or not msg_ids:
        logger.info("✉️ Удаление писем отключено или нечего удалять.")
        return

    try:
        logger.info(f"🗑 Удаляем письма (перемещаем в корзину), всего: {len(msg_ids)}")
        mailbox = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mailbox.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        mailbox.select("inbox")
        for msg_id in msg_ids:
            mailbox.store(msg_id, '+X-GM-LABELS', '\\Trash')  # Gmail way
        mailbox.logout()
        logger.info("✅ Письма успешно перемещены в корзину.")
    except Exception as e:
        logger.exception("❌ Ошибка при удалении писем:")


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        logger.info("📤 Отправляем отчет в Telegram...")
        resp = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"})
        resp.raise_for_status()
        logger.info("✅ Сообщение успешно отправлено в Telegram.")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Ошибка при отправке Telegram-сообщения: {e}")
        logger.debug(f"Ответ от Telegram: {resp.text if 'resp' in locals() else 'Нет ответа'}")


if __name__ == "__main__":
    logger.info("🚀 Запуск скрипта проверки почты и форм...")
    all_emails = fetch_recent_messages()
    result_report, debug_output, matched_msg_ids = check_forms(all_emails)

    logger.info("📊 Результаты проверки:")
    logger.info("\n" + result_report)
    logger.info("\n📋 Подробности:\n" + debug_output)

    send_telegram_message("<b>Результат проверки форм:</b>\n" + result_report)

    delete_emails(matched_msg_ids)
    logger.info("🏁 Скрипт завершен.")
