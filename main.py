import asyncio
import pickle
from selenium import webdriver
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import os
import sys
import logging

#from ddata import LOG, PAS

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Путь к geckodriver
if getattr(sys, 'frozen', False):  # Если программа запущена как exe
    geckodriver_path = os.path.join(sys._MEIPASS, 'web_drivers', 'geckodriver.exe')
else:  # Если программа запущена в режиме разработки
    geckodriver_path = os.path.join(os.path.dirname(__file__), 'web_drivers', 'geckodriver.exe')

logger.info(f"Используется драйвер: {geckodriver_path}")

Progul = 0
# Постоянные переменные
n = "нет"
m = "мед.справка"
o = "объяснительная"
d = "общественная деятельность"
dolv2 = 3  # Начальный индекс столбца
# Описание причин
reasons = {
    'n': "нет (не указана причина)",
    'm': "мед.справка",
    'o': "объяснительная",
    'd': "общественная деятельность"
}

# Функция валидации целого числа
def validate_int(prompt, min_value=None, max_value=None):
    while True:
        try:
            value = int(input(prompt))
            if (min_value is not None and value < min_value) or (max_value is not None and value > max_value):
                print(f"Введите число от {min_value} до {max_value}.")
                continue
            return value
        except ValueError:
            print("Введите корректное число.")

# Функция для ввода строк
def validate_string(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Значение не может быть пустым.")

# Загрузка предыдущих данных
data_file = "config.json"
if os.path.exists(data_file):
    with open(data_file, "r", encoding="utf-8") as file:
        previous_data = json.load(file)
        logger.info("[Предыдущие данные загружены]")
else:
    previous_data = {}
LOG = validate_string(f"Введите логин для PSK (Предыдущее: {previous_data.get('LOG', 'отсутствует')}): ") or previous_data.get('LOG', '')
PAS = validate_string(f"Введите пароль для PSK (Предыдущее: {previous_data.get('PAS', 'отсутствует')}): ") or previous_data.get('PAS', '')

Mount = validate_int(f"Введите месяц (число от 1 до 12, Предыдущее: {previous_data.get('Mount', '')}): ", 1, 12)
Day = validate_int(f"Введите день (число от 1 до 31, Предыдущее: {previous_data.get('Day', '')}): ", 1, 31)
Students_input = validate_string("Введите номера студентов через запятую (например: 1,2,3): ")
Students = [int(s.strip()) for s in Students_input.split(",")]
Progul = validate_int(f"Введите 1 для добавления прогулов или 0 для пропуска (Предыдущее: {previous_data.get('Progul', 0)}): ", 0, 1)

# Выбор причины прогула
PRIC = None
if Progul == 1:
    logger.info("Выберите причину прогула:")
    for key, desc in reasons.items():
        print(f"{key}: {desc}")
    while True:
        PRIC_input = input("Введите причину прогула (n, m, o, d): ").strip().lower()
        if PRIC_input in reasons:
            PRIC = {'n': 'нет', 'm': 'мед.справка', 'o': 'объяснительная', 'd': 'общественная деятельность'}[PRIC_input]
            break
        else:
            logger.warning("Неверный ввод.")
else:
    PRIC = None

# Сохранение данных
with open(data_file, "w", encoding="utf-8") as file:
    json.dump({
        "LOG": LOG,
        "PAS": PAS,
        "Mount": Mount,
        "Day": Day,
        "Students_input": Students_input,
        "Progul": Progul,
    }, file, ensure_ascii=False, indent=4)
    logger.info("Конфигурация сохранена")

# Асинхронная обработка студента
async def process_student(student):
    dolv2_local = 3  # Локальная переменная для столбцов
    options = webdriver.FirefoxOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')  # Скрываем автоматизацию
    browser: WebDriver = webdriver.Firefox(options=options)
    try:
        link = "https://system.fgoupsk.ru/student/login "
        link2 = f"https://system.fgoupsk.ru/student/?mode=ucheba&act=group&act2=prog&m= {Mount}&d={Day}"

        logger.info(f"[Студент {student}] Открытие страницы логина")
        browser.get(link)

        logger.info(f"[Студент {student}] Ввод логина/пароля и вход")
        browser.find_element(By.ID, "input_id").send_keys(LOG)
        browser.find_element(By.ID, "input_password").send_keys(PAS)
        browser.find_element(By.ID, "input_submit").click()

        # Попытка нажать на кнопку всплывающего окна (если есть)
        try:
            logger.info(f"[Студент {student}] Попытка закрыть всплывающее окно")
            WebDriverWait(browser, 2).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.password-checkup-dialog .ok-button'))
            ).click()
        except:
            logger.warning(f"[Студент {student}] Всплывающее окно не найдено или не кликабельно — продолжаем работу")

        # Сохраняем куки
        cookie_file = f"cookie_{student}.pkl"
        logger.info(f"[Студент {student}] Сохранение кук в {cookie_file}")
        pickle.dump(browser.get_cookies(), open(cookie_file, "wb"))

        # Переход на link2
        logger.info(f"[Студент {student}] Переход на страницу прогулов")
        browser.get(link2)

        # Загружаем куки и повторно открываем страницу
        if os.path.exists(cookie_file):
            cookies = pickle.load(open(cookie_file, "rb"))
            for cookie in cookies:
                browser.add_cookie(cookie)
        browser.get(link2)

        # Основные действия с таблицей
        rows = len(browser.find_elements(By.XPATH, f"//tbody/tr[{student}]/td[@data-nb]"))
        logger.info(f"[Студент {student}] Найдено {rows} ячеек прогулов")

        def dangers1():
            nonlocal dolv2_local
            arr1 = browser.find_element(By.XPATH, f"//tbody/tr[{student}]/td[{dolv2_local}]").text
            if arr1 != "-":
                logger.debug(f"[Студент {student}, Ячейка {dolv2_local}] Прогул уже стоит — заменяем")
                browser.find_element(By.XPATH, f"//tbody/tr[{student}]/td[{dolv2_local}]").click()
                browser.find_element(By.ID, "check_nb").click()
                browser.find_element(By.XPATH, "//button[text()='Сохранить']").click()

        def dangers2():
            nonlocal dolv2_local
            arr = browser.find_element(By.XPATH, f"//tbody/tr[{student}]/td[{dolv2_local}]").text
            if arr == "-" or arr in [n, m, o, d]:
                logger.debug(f"[Студент {student}, Ячейка {dolv2_local}] Установка прогула")
                browser.find_element(By.XPATH, f"//tbody/tr[{student}]/td[{dolv2_local}]").click()
                browser.find_element(By.ID, "check_nb").click()
                browser.find_element(By.XPATH, "//button[text()='Сохранить']").click()

        def dangers3():
            if PRIC:
                logger.debug(f"[Студент {student}, Ячейка {dolv2_local}] Выбор причины: {PRIC}")
                browser.find_element(By.XPATH, f"//tbody/tr[{student}]/td[@class='danger']").click()
                browser.find_element(By.ID, "select_type").click()
                browser.find_element(By.XPATH, f"//option[text()='{PRIC}']").click()
                browser.find_element(By.ID, "select_type").click()
                browser.find_element(By.XPATH, "//button[text()='Сохранить']").click()

        for c in range(rows):
            if Progul == 1:
                dangers1()
                dolv2_local += 1
                dangers3()
            else:
                dangers2()
                dolv2_local += 1

    except Exception as e:
        logger.error(f"[Студент {student}] Ошибка: {e}", exc_info=True)
    finally:
        logger.info(f"[Студент {student}] Браузер закрыт")
        browser.quit()

# Главная асинхронная функция
async def main():
    tasks = [process_student(student) for student in Students]
    await asyncio.gather(*tasks)

# Запуск программы
if __name__ == "__main__":
    logger.info("Запуск программы")
    asyncio.run(main())