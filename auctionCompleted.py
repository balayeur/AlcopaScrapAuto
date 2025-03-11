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
if __name__ == "__main__":
    auctions = find_completed_auctions()
    print("Завершённые аукционы на сегодня:")
    for _, linkLive, _, _, _ in auctions:
        print(linkLive)
    save_html_pages(auctions)
