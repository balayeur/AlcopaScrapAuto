import sqlite3
import requests
import time
from datetime import datetime
import re
import os
from WebScraper import WebScraper

DB_FILE = "auctions.db"  # Укажите имя вашей базы данных
SAVE_DIR = "auction_pages"  # Директория для сохранения страниц

os.makedirs(SAVE_DIR, exist_ok=True)  # Создание директории, если её нет

def sanitize_filename(filename, max_length=255):
    """Удаляет недопустимые символы для Windows, MacOS и Linux и обрезает имя файла до допустимой длины."""
    # Недопустимые символы для Windows и некоторых систем Unix
    invalid_chars = r'[<>:"/\\|?*\x00-\x1F]'
    sanitized = re.sub(invalid_chars, '-', filename)

    # Обрезаем имя файла, чтобы не превысить максимальную длину пути
    return sanitized[:max_length]

def find_completed_auctions():
    """Находит завершённые аукционы с сегодняшней датой и возвращает link, linkLive и дату аукциона."""
    today = datetime.today().strftime("%Y-%m-%d")
    # today = "2025-02-11"
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT link, linkLive, date, description, location FROM auctions
        WHERE status = 'Terminé'
    """)
    
    completed_auctions = []
    for row in cursor.fetchall():
        link, linkLive, date, descr, location = row
        if date.startswith(today):  # Учитываем оба формата даты
            completed_auctions.append((link, linkLive, date, descr, location))
    
    conn.close()
    return completed_auctions

def extract_live_id(link):
    """Извлекает идентификационный номер live из поля link."""
    match = re.search(r'/(\d+)(?:\?|$)', link)
    return match.group(1) if match else "unknown"

def save_html_pages(auctions):
    # Создаем объект класса
    scraper = WebScraper(
        login_url="https://www.alcopa-auction.fr/login",
        email="balayeur@hotmail.com",
        password="mironchikova"
    )
    if len(auctions) > 0:
        True
        # Запускаем драйвер и выполняем логин
        scraper.start_driver()
        scraper.login()
        scraper.load_cookies()

    """Проходит по списку ссылок, загружает страницы с паузой в 10 секунд и сохраняет их локально."""
    for link, linkLive, date, descr, location in auctions:
        try:
            if location == "Madrid":
                print(f"Пропускаем аукцион в Мадриде: {descr} {linkLive}")
                continue

            live_id = extract_live_id(link)

            # Формируем безопасное имя файла
            filename = f"{date}_{live_id}_{location}_{descr}.html"
            filename = sanitize_filename(filename)
            save_path = os.path.join("Session", "SavedPage", filename)           
            scraper.save_page_source(linkLive, save_path)

            # response = requests.get(linkLive)
            # response.raise_for_status()
            
            # file_name = f"auction_{date}_{live_id}.html"
            # file_path = os.path.join(SAVE_DIR, file_name)

            # with open(file_path, "w", encoding="utf-8") as file:
            #     file.write(response.text)
            # print(f"Сохранено: {file_path}")
            time.sleep(10)  # Пауза в 10 секунд

        except requests.RequestException as e:
            print(f"Ошибка загрузки {linkLive}: {e}")

    # today = datetime.today().strftime("%Y-%m-%d")
    # categories = ["car", "utility", "gear", "moped", "broken"]
    # for category in categories:
    #     filename = f"{today}_{category}.html"
    #     save_path = os.path.join("Session", "SavedPage", filename)
    #     scraper.save_page_source(f"https://www.alcopa-auction.fr/recherche#{category}", save_path)
    #     time.sleep(10)  # Pause de 10 secondes entre chaque requête

    # Завершаем работу с драйвером
    scraper.quit()

if __name__ == "__main__":
    auctions = find_completed_auctions()
    print("Завершённые аукционы на сегодня:")
    for _, linkLive, _, _, _ in auctions:
        print(linkLive)
    save_html_pages(auctions)
