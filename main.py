import requests
import sqlite3
import datetime
import locale
from bs4 import BeautifulSoup

URL = "https://www.alcopa-auction.fr/"
DB_FILE = "auctions.db"

# Устанавливаем французскую локаль для работы с датами
locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
# locale.setlocale(locale.LC_TIME, "C.UTF-8")


# Словарь для преобразования названий месяцев
MONTHS_FR = {
    "janv.": "01", "févr.": "02", "mars": "03", "avr.": "04",
    "mai": "05", "juin": "06", "juil.": "07", "août": "08",
    "sept.": "09", "oct.": "10", "nov.": "11", "déc.": "12"
}

def fetch_html(url):
    """Загружает HTML-страницу с веб-сайта."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Проверяем ошибки запроса
    return BeautifulSoup(response.text, "html.parser")

def create_database():
    """Создает таблицу, если она не существует."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auctions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            location TEXT,
            lots TEXT,
            date TEXT,
            link TEXT UNIQUE,
            linkLive TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_into_database(category, location, lots, date, link, linkLive):
    """Вставляет данные в базу, если записи еще нет."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO auctions (category, location, lots, date, link, linkLive)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (category, location, lots, date, link, linkLive))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"⚠ Запись уже существует: {location} - {date} - {link} - {linkLive}")
    conn.close()

def convert_timestamp(ts):
    """Конвертирует UNIX timestamp в дату."""
    return datetime.datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")

def convert_french_date(date_str):
    """Конвертирует дату 'lun. 10 févr.' в 'YYYY-MM-DD'."""
    parts = date_str.split()
    if len(parts) != 3:
        return "Non précisé"
    day = parts[1]
    month = MONTHS_FR.get(parts[2], "00")
    year = datetime.datetime.now().year
    return f"{year}-{month}-{day.zfill(2)}"

def parse_sales(soup):
    """Парсит веб-страницу."""
    sales = {"Vente en Salle": [], "Vente Web": [], "Vente de matériel en salle": []}
    for row in soup.find_all("div", class_="row"):
        cols = row.find_all("div", class_="col-md-12", recursive=False)
        if len(cols) < 2:
            continue
        h4 = cols[0].find("h4")
        if not h4:
            continue
        category_name = h4.get_text(strip=True)
        if "Vente en Salle" in category_name:
            sale_category = "Vente en Salle"
        elif "Vente Web" in category_name: # or "Vente web Madrid" in category_name:
            sale_category = "Vente Web"
        elif "Vente de matériel en salle" in category_name:
            sale_category = "Vente de matériel en salle"
        else:
            continue
        for col in cols[1:]:
            div = col.find("div", class_="d-table w-100 mb-2 rounded border no-decoration bg-graylight")
            if not div:
                continue
            try:
                location = div.find("span", class_="font-weight-bold").text.strip()
                lots = div.find("span", class_="text-graynorm").text.strip()
                date = "Non précisé"
                # link = div.find("a", class_="sale-access-href")["href"]
                # link = "https://www.alcopa-auction.fr" + div.find("a", class_="sale-access-href")["href"]
                link = URL + div.find("a", class_="sale-access-href")["href"].lstrip("/")
                linkLiveSale = "Non précisé"

                if sale_category == "Vente Web":
                    ts_span = div.find("span", class_="js-countdown-time")
                    if ts_span and ts_span.has_attr("data-ts"):
                        date = convert_timestamp(ts_span["data-ts"])
                elif sale_category == "Vente en Salle":
                    date_tag = div.find("div", class_="float-right")
                    if date_tag:
                        date = convert_french_date(date_tag.text.strip())
                    # Формируем ссылку live
                    parts = link.split("/")
                    city = parts[4]  # Название города (например, "beauvais")
                    sale_id = parts[5]  # Номер (например, "8058")                    
                    linkLiveSale = f"https://live-{city}.alcopa-auction.fr/{sale_id}"
                sale_data = (location, lots, date, link, linkLiveSale)
                if sale_data not in sales[sale_category]:
                    sales[sale_category].append(sale_data)
            except AttributeError:
                continue
    return sales

def main():
    create_database()
    soup = fetch_html(URL)
    sales_data = parse_sales(soup)
    for category, items in sales_data.items():
        print(f"\n🔹 {category}:")
        for sale in items:
            print(f"📍 {sale[0]} - {sale[1]} - {sale[2]} - 🔗 {sale[3]} - 🔗 {sale[4]}")
            insert_into_database(category, sale[0], sale[1], sale[2], sale[3], sale[4])

if __name__ == "__main__":
    main()
