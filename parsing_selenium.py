import time
import pandas as pd
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, WebDriverException

logging.basicConfig(
    filename='parser.log',
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.info("=== Парсер hh.ru запущен ===")

search = [
    "python разработчик",
    "java разработчик",
    "C# developer",
    "frontend разработчик",
    "backend разработчик",
    "fullstack",
    "системный администратор",
    "сетевой инженер",
    "devops",
    "инженер по тестированию",
    "бизнес-аналитик",
    "системный аналитик",
    "data analyst",
    "data scientist",
    "ИТ-менеджер",
    "руководитель проекта",
    "product manager",
    "project manager",
    "ИТ-консультант",
    "sales manager",
    "account manager",
    "развитие бизнеса",
    "системный архитектор",
    "системный интегратор",
    "специалист по продажам",
    "специалист по сервисам"
]

mp = 15
area = 1

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=chrome_options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

all_vacancies = []


def extract_text_or_none(element, by, value):
    try:
        return element.find_element(by, value).text.strip()
    except NoSuchElementException:
        return None


def parse_vacancy_page(vacancy_url):
    try:
        driver.get(vacancy_url)
        time.sleep(1.2)
        title = extract_text_or_none(driver, By.TAG_NAME, "h1") or "Не указано"
        company = "Не указано"
        try:
            company = driver.find_element(By.CSS_SELECTOR, 'a[data-qa="vacancy-company-name"]').text.strip()
        except:
            try:
                company = driver.find_element(By.CSS_SELECTOR, 'span[data-qa="vacancy-company-name"]').text.strip()
            except:
                pass
        salary = extract_text_or_none(driver, By.CSS_SELECTOR, 'span[data-qa="vacancy-salary-compensation-type-net"]')
        if not salary:
            salary = extract_text_or_none(driver, By.CSS_SELECTOR, 'span[data-qa="vacancy-salary"]') or "Не указана"
        experience = extract_text_or_none(driver, By.CSS_SELECTOR, 'span[data-qa="vacancy-experience"]') or "Не указан"
        city = "Не указан"
        try:
            addr = driver.find_element(By.CSS_SELECTOR, 'p[data-qa="vacancy-view-location"], span[data-qa="vacancy-view-raw-address"]').text
            city = addr.split(',')[0].strip()
        except:
            pass
        description = extract_text_or_none(driver, By.CSS_SELECTOR, 'div[data-qa="vacancy-description"]') or "Описание отсутствует"
        skills = []
        try:
            skill_elements = driver.find_elements(By.CSS_SELECTOR, 'span[data-qa="bloko-tag__text"]')
            skills = [s.text.strip() for s in skill_elements if s.text.strip()]
        except:
            pass
        skills_str = ", ".join(skills) if skills else "Нет навыков"
        return {
            "Название": title,
            "Компания": company,
            "ЗП": salary,
            "Опыт": experience,
            "Описание": description,
            "Ключевые навыки": skills_str,
            "Город": city,
            "Поисковый запрос": current_query
        }
    except WebDriverException as e:
        logging.error(f"Ошибка при парсинге вакансии {vacancy_url}: {e}")
        return None


def parse_search_page(query):
    global current_query
    current_query = query
    logging.info(f"Начинаю парсить запрос: {query}")
    url = f"https://hh.ru/search/vacancy?text={query}&area={area}"
    driver.get(url)
    time.sleep(2)
    for page in range(mp):
        if page > 0:
            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, 'a[data-qa="pager-next"]')
                next_btn.click()
                time.sleep(2)
            except:
                print("Больше страниц нет")
                logging.info(f"Страницы для '{query}' закончились")
                break
        try:
            links = driver.find_elements(By.CSS_SELECTOR, 'a[data-qa="serp-item__title"]')
            vacancy_urls = [link.get_attribute('href') for link in links if link.get_attribute('href')]
        except Exception as e:
            logging.warning(f"Не удалось получить вакансии на странице {page+1}: {e}")
            continue
        for url in vacancy_urls:
            data = parse_vacancy_page(url)
            if data:
                all_vacancies.append(data)
                print(f"[{len(all_vacancies)}] {data['Название']} | {data['Компания']}")
                logging.info(f"Собрана вакансия: {data['Название']} ({data['Компания']})")
try:
    for query in search:
        parse_search_page(query)
finally:
    driver.quit()

if all_vacancies:
    df = pd.DataFrame(all_vacancies, columns=[
        "Название", "Компания", "ЗП", "Опыт", "Описание",
        "Ключевые навыки", "Город", "Поисковый запрос"
    ])
    df.to_csv("hh_vacancies.csv", index=False)
    print(" Парсер завершил работу успешно!")
    print(f"Всего собрано вакансий: {len(all_vacancies)}")
    logging.info(f"Парсер завершил работу. Всего {len(all_vакансий)} вакансий.")
else:
    print("Ничего не спарсил. Проверь интернет или уменьшай количество страниц.")
    logging.warning("Парсер не собрал ни одной вакансии")

print("Работа парсера закончена")
