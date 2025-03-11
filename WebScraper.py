from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import pickle
import time


class WebScraper:
    def __init__(self, login_url, email, password, cookies_file="cookies.pkl"):
        self.login_url = login_url
        self.email = email
        self.password = password
        self.cookies_file = cookies_file
        self.driver = None

    def start_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--no-first-run")  # Отключает окно первого запуска
        chrome_options.add_argument("--disable-infobars")  # Отключает всплывающие уведомления
        self.driver = webdriver.Chrome(options=chrome_options)

    def login(self):
        if self.driver is None:
            raise ValueError("Driver is not started. Please call start_driver() first.")

        self.driver.get(self.login_url)

        # Находим поля ввода
        username_input = self.driver.find_element(By.NAME, "email")
        password_input = self.driver.find_element(By.NAME, "password")
        
        # username_input = self.driver.find_element(By.NAME, "login[email]")
        # password_input = self.driver.find_element(By.NAME, "login[password]")

        # Вводим логин и пароль
        username_input.send_keys(self.email)
        password_input.send_keys(self.password)
        password_input.send_keys(Keys.RETURN)

        time.sleep(15)  # Ждем загрузки страницы

        # Сохраняем cookies в файл
        with open(self.cookies_file, "wb") as file:
            pickle.dump(self.driver.get_cookies(), file)

    def load_cookies(self):
        if self.driver is None:
            raise ValueError("Driver is not started. Please call start_driver() first.")

        # Загружаем cookies из файла
        try:
            with open(self.cookies_file, "rb") as file:
                cookies = pickle.load(file)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
        except FileNotFoundError:
            print("Cookies файл не найден. Необходимо авторизоваться заново.")

    def save_page_source(self, url, save_path):
        if self.driver is None:
            raise ValueError("Driver is not started. Please call start_driver() first.")

        # Открываем страницу
        self.driver.get(url)
        time.sleep(5)  # Ждем загрузки страницы

        # Сохраняем исходный код HTML
        page_source = self.driver.page_source
        with open(save_path, "w", encoding="utf-8") as file:
            file.write(page_source)
        print(f"Сохранено: {save_path}")

    def save_multiple_pages(self, urls):
        if self.driver is None:
            raise ValueError("Driver is not started. Please call start_driver() first.")

        for idx, url in enumerate(urls):
            save_path = f"Session/page_{idx + 1}.html"
            self.save_page_source(url, save_path)
            time.sleep(10)  # Пауза между запросами

    def quit(self):
        if self.driver:
            self.driver.quit()


