from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

DB_FILE = "auctions.db"

def fetch_auctions():
    """Извлекает аукционы из базы данных, разделяя активные и завершенные."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Активные аукционы (En cours), сортируем по дате возрастанию
    cursor.execute("SELECT * FROM auctions WHERE status = 'En cours' ORDER BY date ASC")
    active_auctions = cursor.fetchall()

    # Завершенные аукционы (Terminé), сортируем по дате убыванию
    cursor.execute("SELECT * FROM auctions WHERE status = 'Terminé' ORDER BY date DESC")
    finished_auctions = cursor.fetchall()

    conn.close()
    return active_auctions, finished_auctions

@app.route("/")
def index():
    """Главная страница с отображением всех аукционов."""
    active_auctions, finished_auctions = fetch_auctions()
    return render_template("index.html", active_auctions=active_auctions, finished_auctions=finished_auctions)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
