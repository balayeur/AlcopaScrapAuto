from fastapi import FastAPI, HTTPException
import sqlite3

DB_FILE = "auctions.db"

app = FastAPI(title="Auction Sales API", description="API для получения информации о продажах Alcopa Auction")

def get_sales(category: str = None):
    """Получает данные из БД по категории или все записи."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if category:
        cursor.execute("SELECT category, location, lots, date, link FROM auctions WHERE category = ?", (category,))
    else:
        cursor.execute("SELECT category, location, lots, date, link FROM auctions")
    
    sales = cursor.fetchall()
    conn.close()
    
    return [
        {"category": row[0], "location": row[1], "lots": row[2], "date": row[3], "link": row[4]} for row in sales
    ]

@app.get("/sales/all", summary="Получить все продажи")
def get_all_sales():
    sales = get_sales()
    if not sales:
        raise HTTPException(status_code=404, detail="Нет данных о продажах")
    return sales

@app.get("/sales/room", summary="Получить продажи Vente en Salle")
def get_room_sales():
    sales = get_sales("Vente en Salle")
    if not sales:
        raise HTTPException(status_code=404, detail="Нет данных о продажах в зале")
    return sales

@app.get("/sales/web", summary="Получить продажи Vente Web")
def get_web_sales():
    sales = get_sales("Vente Web")
    if not sales:
        raise HTTPException(status_code=404, detail="Нет данных о продажах в вебе")
    return sales

@app.get("/sales/material", summary="Получить продажи Vente de matériel en salle")
def get_material_sales():
    sales = get_sales("Vente de matériel en salle")
    if not sales:
        raise HTTPException(status_code=404, detail="Нет данных о продажах оборудования")
    return sales

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
