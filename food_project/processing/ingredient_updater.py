import sys
import sqlite3
from food_project.processing.normalization import parse_ingredient

DB_PATH = "food_info.db"

def update_ingredients(force=False):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute("ALTER TABLE ingredients ADD COLUMN estimated_grams REAL")
    except: pass
    try:
        cur.execute("ALTER TABLE ingredients ADD COLUMN fuzz_score REAL")
    except: pass

    rows = cur.execute("SELECT id, name FROM ingredients" + ("" if force else " WHERE normalized_name IS NULL")).fetchall()

    updated = 0
    for ing_id, raw_text in rows:
        amount, unit, normalized_name, est_grams = parse_ingredient(raw_text)
        cur.execute("""
            UPDATE ingredients
            SET amount = ?, unit = ?, normalized_name = ?, estimated_grams = ?
            WHERE id = ?
        """, (amount, unit, normalized_name, est_grams, ing_id))
        updated += 1

    conn.commit()
    conn.close()
    print(f"✅ Updated {updated} ingredient(s). {'(forced)' if force else '(new only)'}")

if __name__ == "__main__":
    update_ingredients(force="--force" in sys.argv)