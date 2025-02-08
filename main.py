import requests
import sqlite3
import time
from bs4 import BeautifulSoup

# URL целевой страницы
URL = "https://www.alcopa-auction.fr/"

# Инициализация базы данных
DB_FILE = "sales.db"

def init_db():
    """Создаёт таблицу в SQLite, если её нет."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS sales (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT,
                        title TEXT,
                        date TEXT,
                        price TEXT,
                        UNIQUE(category, title, date)
                    )''')
    conn.commit()
    conn.close()

def fetch_page():
    """Загружает HTML страницы."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(URL, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        print("Ошибка загрузки страницы:", response.status_code)
        return None

def parse_sales(html):
    """Парсит HTML и извлекает данные о продажах."""
    soup = BeautifulSoup(html, "lxml")
    sales_data = []

    categories = {
        "Vente en Salle": "vente-en-salle-class",
        "Vente Web": "vente-web-class",
        "Vente de matériel en salle": "vente-materiel-class"
    }

    for category, class_name in categories.items():
        sales = soup.find_all("div", class_=class_name)  # Найти блоки продаж

        for sale in sales:
            title = sale.find("h2").text.strip() if sale.find("h2") else "Без названия"
            date = sale.find("span", class_="date").text.strip() if sale.find("span", class_="date") else "Неизвестно"
            price = sale.find("span", class_="price").text.strip() if sale.find("span", class_="price") else "Не указана"

            sales_data.append((category, title, date, price))

    return sales_data

def save_to_db(sales_data):
    """Сохраняет новые записи в базу данных."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    new_entries = 0

    for sale in sales_data:
        try:
            cursor.execute("INSERT INTO sales (category, title, date, price) VALUES (?, ?, ?, ?)", sale)
            new_entries += 1
        except sqlite3.IntegrityError:
            pass  # Пропускаем уже существующие записи

    conn.commit()
    conn.close()
    print(f"Добавлено новых записей: {new_entries}")

def main():
    """Основной цикл работы."""
    init_db()
    while True:
        print("🔄 Запуск парсинга...")
        html = fetch_page()
        if html:
            sales_data = parse_sales(html)
            save_to_db(sales_data)
        print("⏳ Ожидание 30 минут перед следующим запуском...")
        time.sleep(1800 * 100)  # 30 минут

if __name__ == "__main__":
    main()