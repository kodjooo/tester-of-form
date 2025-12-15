import asyncio
import logging
import os
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Настройка логирования (пишем в директорию из переменной окружения LOG_DIR)
LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "forms_test.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8"
)

TEST_DATA = {
    "name": "Тестовый Марк",
    "email": "mark.aborchi@gmail.com",
    "phone": "40000000",
    "website": "https://meta-test.com/"
}

async def fill_and_submit_form(page, form_type, url, popup_button=None):
    try:
        logging.info(f"[{form_type}] Переход на страницу: {url}")
        await page.goto(url, wait_until="load", timeout=60000)
        logging.info(f"[{form_type}] Страница загружена")

        if form_type == "Форма 5":
            try:
                logging.info(f"[{form_type}] Ожидание кнопки согласия: #accept-consents")
                await page.wait_for_selector(".co__footer #accept-consents", timeout=10000)
                await page.click("#accept-consents")
                logging.info(f"[{form_type}] Кнопка согласия нажата")
            except Exception as e:
                logging.warning(f"[{form_type}] Не удалось нажать кнопку согласия: {e}")

        popup_form = None
        if popup_button:
            try:
                logging.info(f"[{form_type}] Ожидание кнопки попапа: {popup_button}")
                await page.wait_for_selector(popup_button, timeout=15000)
                await page.click(popup_button)
                logging.info(f"[{form_type}] Попап открыт кнопкой {popup_button}")

                if form_type == "Форма 5":
                    popup_container_selector = "amp-lightbox#consultation"
                    await page.wait_for_function(
                        """() => {
                            const el = document.querySelector('#consultation');
                            return el && window.getComputedStyle(el).opacity === '1';
                        }""",
                        timeout=15000
                    )
                else:
                    popup_container_selector = "#modal_consult"
                    await page.wait_for_selector(popup_container_selector, timeout=15000, state="visible")

                popup_container = await page.query_selector(popup_container_selector)
                popup_form = await popup_container.query_selector("form")
                if not popup_form:
                    raise Exception("Форма в попапе не найдена")

                logging.info(f"[{form_type}] Форма внутри попапа доступна")

            except Exception as e:
                msg = f"[{form_type}] Ошибка при открытии попапа или получении формы: {e}"
                logging.error(msg)
                return False, msg

        form_scope = popup_form if popup_form else page

        async def try_fill(selector, value):
            try:
                logging.info(f"[{form_type}] Заполнение поля {selector} значением '{value}'")
                input_el = await form_scope.wait_for_selector(selector, state="visible", timeout=10000)
                await input_el.fill(value)
                logging.info(f"[{form_type}] Поле {selector} успешно заполнено")
                return True
            except TimeoutError as e:
                logging.warning(f"[{form_type}] Поле {selector} не найдено или невидимо")
                return False
            except PlaywrightTimeoutError:
                logging.warning(f"[{form_type}] Поле {selector} не найдено или невидимо")
                return False

        email_filled = await try_fill("input[name='email']", TEST_DATA["email"])
        if not email_filled:
            await try_fill("input[name='SubscribeForm[email]']", TEST_DATA["email"])

        if form_type == "Форма 5":
            phone_value = "+79994000000"
        elif form_type == "Форма 6":
            phone_value = "+79994000001"
        elif form_type == "Форма 3":
            phone_value = "41111111"
        elif form_type == "Форма 4":
            phone_value = "41111112"
        else:
            phone_value = TEST_DATA["phone"]

        phone_filled = await try_fill("input[type='tel']", phone_value)
        if not phone_filled:
            phone_filled = await try_fill("input[name='phone']", phone_value)
        if not phone_filled:
            await try_fill("input[name='SubscribeForm[phone]']", phone_value)

        await try_fill("input[name='SubscribeForm[name]']", TEST_DATA["name"])
        await try_fill("input[name='SubscribeForm[website]']", TEST_DATA["website"])

        checkbox_selector = "input[type='checkbox']"
        checkbox = await form_scope.query_selector(checkbox_selector)

        if checkbox:
            visible = await checkbox.is_visible()
            enabled = await checkbox.is_enabled()
            logging.info(f"[{form_type}] Найден чекбокс: видим={visible}, активен={enabled}")

            if visible and enabled:
                try:
                    label = None
                    if form_type == "Форма 5":
                        label = await form_scope.query_selector("label[for='consultation-terms']")
                    else:
                        checkbox_id = await checkbox.get_attribute("id")
                        if checkbox_id:
                            label = await form_scope.query_selector(f"label[for='{checkbox_id}']")
                        if not label:
                            label = await checkbox.evaluate_handle("el => el.closest('label')")

                    if label:
                        await label.evaluate("""
                            el => {
                                const rect = el.getBoundingClientRect();
                                const event = new MouseEvent('click', {
                                    bubbles: true,
                                    cancelable: true,
                                    view: window,
                                    clientX: rect.left + rect.width / 2,
                                    clientY: rect.top + rect.height / 2
                                });
                                el.dispatchEvent(event);
                            }
                        """)
                        logging.info(f"[{form_type}] Чекбокс успешно отмечен")
                    else:
                        raise Exception("Label не найден")

                except Exception as e:
                    logging.error(f"[{form_type}] Ошибка при попытке отметить чекбокс: {e}")
            else:
                logging.warning(f"[{form_type}] Чекбокс недоступен для отметки")
        else:
            logging.warning(f"[{form_type}] Чекбокс не найден")

        if form_type == "Форма 5":
            try:
                label_option_web = await form_scope.wait_for_selector("label[for='option-web']", timeout=5000)
                await label_option_web.evaluate("""
                    el => {
                        const rect = el.getBoundingClientRect();
                        const event = new MouseEvent('click', {
                            bubbles: true,
                            cancelable: true,
                            view: window,
                            clientX: rect.left + rect.width / 2,
                            clientY: rect.top + rect.height / 2
                        });
                        el.dispatchEvent(event);
                    }
                """)
                logging.info(f"[{form_type}] Label 'option-web' успешно нажат")
            except Exception as e:
                logging.warning(f"[{form_type}] Ошибка при клике по 'option-web': {e}")

        async def click_if_exists(selector):
            try:
                logging.info(f"[{form_type}] Поиск кнопки отправки: {selector}")
                btn = await page.wait_for_selector(selector, state="visible", timeout=5000)
                await btn.click(force=True)
                logging.info(f"[{form_type}] Кнопка {selector} нажата")
                return True
            except PlaywrightTimeoutError:
                logging.warning(f"[{form_type}] Кнопка {selector} не найдена или невидима")
                return False
            except Exception as e:
                logging.error(f"[{form_type}] Ошибка при клике по кнопке {selector}: {e}")
                return False

        clicked = await click_if_exists("a.feedback_submit")
        if not clicked:
            clicked = await click_if_exists("a.submit_button")
        if not clicked:
            clicked = await click_if_exists("button[type='submit']")
        if not clicked:
            msg = f"[{form_type}] Не найдена кнопка отправки"
            logging.error(msg)
            return False, msg

        logging.info(f"[{form_type}] Ждём 5 секунд после отправки формы")
        await asyncio.sleep(5)

        success_msg = f"✅ Успешно отправлена форма: {form_type}"
        logging.info(success_msg)
        return True, success_msg

    except Exception as e:
        error_msg = f"❌ Ошибка при обработке формы {form_type}: {e}"
        logging.exception(error_msg)
        return False, error_msg


async def main():
    forms = [
        {"name": "Форма 1", "url": "https://www.metawebart.com/en", "popup_button": "#consultation-button"},
        {"name": "Форма 2", "url": "https://www.metawebart.com/en", "popup_button": None},
        {"name": "Форма 3", "url": "https://www.metawebart.com/en/page/large_projects-ru", "popup_button": "#consultation-button"},
        {"name": "Форма 4", "url": "https://www.metawebart.com/en/page/large_projects-ru", "popup_button": None},
        {"name": "Форма 5", "url": "https://meta-sistem.md", "popup_button": "section#hero .btn"},
        {"name": "Форма 6", "url": "https://meta-sistem.md/ru/web", "popup_button": None}
    ]

    results = []
    async with async_playwright() as p:
        # Управление режимом headless через переменную окружения HEADLESS (true/false)
        headless_env = os.getenv("HEADLESS", "true").lower() == "true"
        browser = await p.chromium.launch(headless=headless_env)
        context = await browser.new_context()
        page = await context.new_page()

        for form in forms:
            logging.info(f"Начинаем обработку {form['name']}")
            success, message = await fill_and_submit_form(
                page,
                form["name"],
                form["url"],
                form.get("popup_button")
            )
            logging.info(f"Результат {form['name']}: {message}")
            results.append(message)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
