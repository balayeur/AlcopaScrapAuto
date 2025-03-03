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

