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
            serving_qty TEXT,
            serving_unit TEXT,
            serving_weight_grams REAL,
            calories REAL,
            fat REAL,
            saturated_fat REAL,
            cholesterol REAL,
            sodium REAL,
            carbs REAL,
            fiber REAL,
            sugars REAL,
            protein REAL,
            potassium REAL
        )
    """)
    conn.commit()

def import_food_data(conn):
    cursor = conn.cursor()
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute("""
                INSERT INTO food_info (
                    name, serving_qty, serving_unit, serving_weight_grams,
                    calories, fat, saturated_fat, cholesterol,
                    sodium, carbs, fiber, sugars, protein, potassium
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row.get("Food Query"),
                row.get("serving_qty"),
                row.get("serving_unit"),
                parse_float(row.get("serving_weight_grams")),
                parse_float(row.get("nf_calories")),
                parse_float(row.get("nf_total_fat")),
                parse_float(row.get("nf_saturated_fat")),
                parse_float(row.get("nf_cholesterol")),
                parse_float(row.get("nf_sodium")),
                parse_float(row.get("nf_total_carbohydrate")),
                parse_float(row.get("nf_dietary_fiber")),
                parse_float(row.get("nf_sugars")),
                parse_float(row.get("nf_protein")),
                parse_float(row.get("nf_potassium")),
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

    # Delete old rows with NULLs (optional, just in case)
    conn.execute("DELETE FROM food_info")
    import_food_data(conn)

    conn.close()
    print("✅ Fixed food info imported successfully.")
