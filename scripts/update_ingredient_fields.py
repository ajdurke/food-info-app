import sqlite3
from pathlib import Path
from food_project.processing.normalization import parse_ingredient

DB_PATH = Path("food_info.db")

def update_all_ingredients():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    rows = cursor.execute("SELECT id, food_name FROM ingredients").fetchall()
    print(f"🔄 Updating {len(rows)} ingredients...\n")

    for row in rows:
        id = row["id"]
        raw_name = row["food_name"]

        amount, unit, normalized_name, est_grams = parse_ingredient(raw_name)

        cursor.execute("""
            UPDATE ingredients
            SET amount = ?, unit = ?, normalized_name = ?, est_grams = ?
            WHERE id = ?
        """, (amount, unit, normalized_name, est_grams, id))

    conn.commit()
    conn.close()
    print("✅ Ingredients table updated with parsed values.")

if __name__ == "__main__":
    update_all_ingredients()
