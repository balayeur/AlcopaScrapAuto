from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pickle
import time
import os


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

    # # Находим поля ввода
    # username_input = self.driver.find_element(By.NAME, "email")
    # password_input = self.driver.find_element(By.NAME, "password")

    # # username_input = self.driver.find_element(By.NAME, "login[email]")
    # # password_input = self.driver.find_element(By.NAME, "login[password]")


    def login(self):
        if self.driver is None:
            raise ValueError("Driver is not started. Please call start_driver() first.")

        # input("1...")
        # Открываем страницу входа
        self.driver.get(self.login_url)
        
        # input("2...")

        # Если есть сохранённые cookies — пытаемся их загрузить и обновить страницу,
        # чтобы избежать капчи/авторизации вручную
        if os.path.exists(self.cookies_file):
            try:
                self.load_cookies()
                self.driver.refresh()
                # print("Cookies загружены, страница обновлена.")
                # Быстрая проверка: уже ли мы залогинены по элементу меню пользователя
                try:
                    WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.menu-user"))
                    )
                    print("Cookies загружены и пользователь уже залогинен — пропускаем вход.")
                    return True
                except TimeoutException:
                    print("Cookies загружены, но пользователь не залогинен — продолжаем обычный вход.")
            except Exception:
                # не критично — продолжим обычный поток
                print("Не удалось загрузить cookies, продолжаем обычный вход.")
                pass

        captcha_selectors = [
            ("recaptcha_iframe", By.CSS_SELECTOR, "iframe[src*='recaptcha']"),
            ("g-recaptcha", By.CSS_SELECTOR, "div.g-recaptcha"),
            ("h-captcha", By.CSS_SELECTOR, "div.h-captcha"),
            ("cloudflare_browser_verification", By.CSS_SELECTOR, "div.cf-browser-verification"),
            # ("text_contains_captcha", By.XPATH, "//*[contains(translate(text(),'CAPTCHA','captcha'),'captcha')]"),
        ]

        # input("3...")

        matched_name = None
        matched_selector = None
        captcha_found = False
        for name, by, sel in captcha_selectors:
            try:
                # очень короткая явная ожидание — просто для быстрой проверки
                WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((by, sel)))
                matched_name = name
                matched_selector = (by, sel)
                captcha_found = True
                print(f"Обнаружена капча: {matched_name} селектор = {matched_selector}")
                break            
            except TimeoutException:
                continue        

        # Если капча обнаружена — просим пользователя пройти её вручную,
        # иначе продолжаем сразу искать pop-up логина.
        if captcha_found:
            print("Появилась капча. Пройдите её вручную в открытом окне браузера.")
            input("После прохождения капчи и появления pop-up для логина нажмите Enter...")

        # Ждём появления полей логина (pop-up). Если их нет — возвращаем False.
        try:
            print("Ожидание появления полей логина...")
            username_input = WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            password_input = self.driver.find_element(By.NAME, "password")
        except Exception as e:
            self.driver.save_screenshot("Session/Log/login_error.png")
            print("Смотри скриншот в логе. Ошибка при выполнении входа:", e)
            return False

        # Заполняем поля и отправляем форму
        if username_input and password_input:
            username_input.clear()
            username_input.send_keys(self.email)
            password_input.clear()
            password_input.send_keys(self.password)
            password_input.send_keys(Keys.RETURN)
        else:
            print("Не удалось найти поля для логина или пароля. Смотри скриншот в логе.")
            self.driver.save_screenshot("Session/Log/login_fields_not_found.png")
            return False

        # Ждём признака успешного входа (например, кнопка выхода/профиль или изменение URL)
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".logout, .profile, .menu-user"))
            )
            print("Вход выполнен успешно.")
        except Exception:
            # Можно также проверить изменение URL или отсутствие поп-up
            print("Вход не выполнен или страница не загрузилась корректно. Смотри скриншот в логе.")
            self.driver.save_screenshot("Session/Log/login_failed.png")
            return False

        # Сохраняем cookies для будущих запусков
        time.sleep(2)
        with open(self.cookies_file, "wb") as file:
            pickle.dump(self.driver.get_cookies(), file)
        return True  # Возвращаем True при успехе


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


