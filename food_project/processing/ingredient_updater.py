import sqlite3
import argparse
from pathlib import Path
from food_project.processing.normalization import parse_ingredient

def update_ingredients(force=False, db_path="food_info.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Add required columns if not already present
    for column_def in [
        "ALTER TABLE ingredients ADD COLUMN amount REAL",
        "ALTER TABLE ingredients ADD COLUMN unit TEXT",
        "ALTER TABLE ingredients ADD COLUMN normalized_name TEXT",
        "ALTER TABLE ingredients ADD COLUMN estimated_grams REAL",
        "ALTER TABLE ingredients ADD COLUMN fuzz_score REAL"
    ]:
        try:
            cur.execute(column_def)
        except sqlite3.OperationalError:
            pass  # Column already exists

    query = "SELECT id, food_name FROM ingredients"
    if not force:
        query += " WHERE normalized_name IS NULL"

    rows = cur.execute(query).fetchall()

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

def main():
    parser = argparse.ArgumentParser(description="Update parsed ingredient data")
    parser.add_argument("--db", default="food_info.db", help="Path to SQLite database")
    parser.add_argument("--force", action="store_true", help="Force reprocessing of all ingredients")
    args = parser.parse_args()

    update_ingredients(force=args.force, db_path=args.db)

if __name__ == "__main__":
    main()
