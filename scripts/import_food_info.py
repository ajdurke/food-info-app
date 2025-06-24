import csv
import sqlite3

DB_PATH = "food_info.db"
CSV_PATH = "food_info_app - Sheet1.csv"

def init_food_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS food_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            calories REAL,
            protein REAL,
            fat REAL,
            carbs REAL,
            water_use_liters REAL,
            carbon_kg REAL
        )
    """)
    conn.commit()

def import_food_data(conn):
    cursor = conn.cursor()
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute("""
                INSERT INTO food_info (name, calories, protein, fat, carbs, water_use_liters, carbon_kg)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                row.get("Food Query") or row.get("Name"),
                parse_float(row.get("Calories")),
                parse_float(row.get("Protein (g)")),
                parse_float(row.get("Fat (g)")),
                parse_float(row.get("Carbs (g)")),
                parse_float(row.get("Water Use (Liters)")),
                parse_float(row.get("Carbon Footprint (kg)"))
            ))
    conn.commit()

def parse_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    init_food_table(conn)
    import_food_data(conn)
    conn.close()
    print("✅ Food info data imported successfully.")
