import requests
import sqlite3
import datetime
import locale
from bs4 import BeautifulSoup

URL = "https://www.alcopa-auction.fr/"
DB_FILE = "auctions.db"
# HTML_FILE = "mnt/data/AlcopaAuction.html"
# HTML_FILE = "/Users/maximebeauger/Projects/PYTHON/AlcopaLaunchAgents/alcopa_2025-02-11_23-35.html"
DIRECTORY = "/Users/maximebeauger/Projects/PYTHON/AlcopaLaunchAgents/"

HTML_FILE = DIRECTORY + "alcopa_2025-02-10_23-35.html"
# HTML_FILE = DIRECTORY + "alcopa_2025-02-11_23-35.html"
HTML_FILE = DIRECTORY + "alcopa_2025-02-12_23-35.html"
HTML_FILE = DIRECTORY + "alcopa_2025-02-13_23-35.html"
HTML_FILE = DIRECTORY + "alcopa_2025-02-14_23-00.html"


# Устанавливаем французскую локаль для работы с датами
locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")

# Словарь для преобразования названий месяцев
MONTHS_FR = {
    "janv.": "01", "févr.": "02", "mars": "03", "avr.": "04",
    "mai": "05", "juin": "06", "juil.": "07", "août": "08",
    "sept.": "09", "oct.": "10", "nov.": "11", "déc.": "12"
}

def load_html(file_path):
    """Загружает HTML и создает объект BeautifulSoup."""
    with open(file_path, "r", encoding="utf-8") as file:
        return BeautifulSoup(file, "html.parser")

def fetch_html(url):
    """Загружает HTML-страницу с веб-сайта."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def create_database():
    """Создает таблицу, если она не существует."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auctions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            description TEXT,
            location TEXT,
            lots TEXT,
            date TEXT,
            link TEXT UNIQUE,
            linkLive TEXT,
            status TEXT DEFAULT 'En cours'
        )
    """)
    conn.commit()
    conn.close()

def insert_or_update_auction(category, description, location, lots, date, link, linkLive):
    """Вставляет новый аукцион или обновляет его статус в базе."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM auctions WHERE link = ?", (link,))
    result = cursor.fetchone()

    if result:
        # Аукцион уже есть, обновляем данные (вдруг дата изменилась)
        cursor.execute("""
            UPDATE auctions
            SET category = ?, description = ?, location = ?, lots = ?, date = ?, linkLive = ?, status = 'En cours'
            WHERE link = ?
        """, (category, description, location, lots, date, linkLive, link))
    else:
        # Новый аукцион, добавляем
        cursor.execute("""
            INSERT INTO auctions (category, description, location, lots, date, link, linkLive, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'En cours')
        """, (category, description, location, lots, date, link, linkLive))

    conn.commit()
    conn.close()

import sqlite3
import datetime

DB_FILE = "auctions.db"


def mark_auctions_as_finished():
    """Отмечает завершенными аукционы, дата которых - вчера или раньше."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    today = datetime.date.today()

    # Выбираем все активные аукционы
    cursor.execute("SELECT id, date FROM auctions WHERE status = 'En cours'")
    active_auctions = cursor.fetchall()

    for auction_id, auction_date in active_auctions:
        try:
            if auction_date in ["En cours", "Non précisé"]:
                continue  # Пропускаем аукционы без четкой даты

            # Попробуем сначала с `HH:MM:SS`, если ошибка - обрабатываем без времени
            try:
                auction_date_obj = datetime.datetime.strptime(auction_date, "%Y-%m-%d %H:%M:%S").date()
            except ValueError:
                auction_date_obj = datetime.datetime.strptime(auction_date, "%Y-%m-%d").date()

            if auction_date_obj < today:  # Если дата прошла
                cursor.execute("UPDATE auctions SET status = 'Terminé' WHERE id = ?", (auction_id,))
                print(f"✅ Аукцион завершен: ID {auction_id}, дата {auction_date}")

        except ValueError as e:
            print(f"⚠ Ошибка обработки даты для ID {auction_id}: {auction_date} ({e})")
            continue

    conn.commit()
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

def generate_live_link(sale_category, location, link):
    """Генерирует ссылку на Live-аукцион в зависимости от категории и местоположения."""
    parts = link.split("/")

    if sale_category == "Vente Web" and len(parts) == 5:
        sale_id = parts[4].split("?")[0]
        return f"https://live-flash.alcopa-auction.fr/{sale_id}/flash-sale"

    if len(parts) < 6:
        return link  # Возвращаем исходную ссылку, если структура некорректная

    city, sale_id = parts[4], parts[5].split("?")[0]

    if location == "Multisite":
        return f"https://www.alcopa-auction.fr/acceder-au-vente-encheres/{sale_id}/FR/1/2"

    if sale_category == "Vente Web":
        return f"https://live-flash.alcopa-auction.fr/{sale_id}/flash-sale"

    return f"https://live-{city}.alcopa-auction.fr/{sale_id}"


def parse_sales(soup):
    """Парсит веб-страницу и извлекает данные об аукционах."""
    sales = {
        "Vente en cours": [],
        "Vente en Salle": [],
        "Vente Web": [],
        # "Vente de 2-roues": [],
        "Vente de matériel en salle": []
    }
    active_links = set()

    category_map = {
        "Vente en Salle": "Vente en Salle",
        "Vente en cours": "Vente en cours",
        "Vente Web": "Vente Web",
        # "Vente de 2-roues": "Vente de 2-roues",
        "Vente de matériel en salle": "Vente de matériel en salle"
    }

    for row in soup.find_all("div", class_="row"):
        for col in row.find_all("div", class_="col-md-12", recursive=False):
            h4 = col.find("h4")
            if not h4:
                continue

            category_name = h4.get_text(strip=True)
            sale_category = category_map.get(category_name)
            if not sale_category:
                continue

            # Ищем аукционы внутри row
            for div in row.find_all("div", class_="d-table w-100 mb-2 rounded border no-decoration bg-graylight"):
                try:
                    location = div.find("span", class_="font-weight-bold").get_text(strip=True)
                    lots = div.find("span", class_="text-graynorm").get_text(strip=True)
                    descr = div.find("div", class_="text-graynorm mt-1 pt-1 border-top lh-20").get_text(strip=True)
                    link = URL + div.find("a", class_="sale-access-href")["href"].lstrip("/")
                    date = "Non précisé"

                    lots = lots.split(" ")[1]  # Оставляем только количество лотов

                    if sale_category == "Vente Web":
                        ts_span = div.find("span", class_="js-countdown-time")
                        if ts_span and ts_span.has_attr("data-ts"):
                            date = convert_timestamp(ts_span["data-ts"])
                        else:
                            date_tag = div.find("div", class_="float-right")
                            if date_tag:
                                date = convert_french_date(date_tag.get_text(strip=True))


                    elif sale_category == "Vente en cours":
                        date = "En cours"

                    elif sale_category == "Vente en Salle" or sale_category == "Vente de matériel en salle":
                        date_tag = div.find("div", class_="float-right")
                        if date_tag:
                            date = convert_french_date(date_tag.get_text(strip=True))

                    linkLiveSale = generate_live_link(sale_category, location, link)

                    active_links.add(link)
                    insert_or_update_auction(sale_category, descr, location, lots, date, link, linkLiveSale)

                except AttributeError:
                    continue  # Пропускаем ошибки парсинга

    return active_links


def main():
    create_database()
    soup = load_html(HTML_FILE)
    # soup = fetch_html(URL)
    active_links = parse_sales(soup)
    mark_auctions_as_finished()

if __name__ == "__main__":
    main()
