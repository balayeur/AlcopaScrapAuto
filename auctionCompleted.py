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
if __name__ == "__main__":
    auctions = find_completed_auctions()
    print("Завершённые аукционы на сегодня:")
    for _, linkLive, _, _, _ in auctions:
        print(linkLive)
    save_html_pages(auctions)
