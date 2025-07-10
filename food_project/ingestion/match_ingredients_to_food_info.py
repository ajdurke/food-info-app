print("🔗 match_ingredients_to_food_info.py loaded")

"""Link parsed ingredients to entries in the ``food_info`` table."""

import sqlite3
import argparse
from food_project.processing.matcher import fetch_db_food_matches
from food_project.database.sqlite_connector import init_db
from pathlib import Path

def match_ingredients(db_path="food_info.db", init=False):
    """Attempt to automatically match ingredients to known foods."""
    conn = sqlite3.connect(db_path)
    if init:
        print("⚙️ init_db() is recreating the food_info table")
        init_db(conn)

    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Add required columns if not already present
    for column_def in [
        "ALTER TABLE ingredients ADD COLUMN fuzz_score REAL",
        "ALTER TABLE ingredients ADD COLUMN match_type TEXT",
        "ALTER TABLE ingredients ADD COLUMN matched_food_id INTEGER"
    ]:
        try:
            cur.execute(column_def)
        except sqlite3.OperationalError:
            pass  # Already exists

    # Load ingredients needing a match
    all_ingredients = cur.execute("SELECT id, normalized_name FROM ingredients").fetchall()
    # ``unmatched_ingredients`` contains rows that haven't been normalized yet
    unmatched_ingredients = [row for row in all_ingredients if not row["normalized_name"]]

    print(f"📊 Total ingredients: {len(all_ingredients)}")
    print(f"🔎 Ingredients needing matching: {len(unmatched_ingredients)}")

    food_entries = cur.execute("SELECT id, normalized_name FROM food_info").fetchall()

    matched = 0
    # Iterate over each ingredient and attempt to find the best match
    for ing in all_ingredients:
        ing_id, ing_name = ing["id"], ing["normalized_name"]
        if not ing_name:
            continue

        # ``fetch_db_food_matches`` returns the best candidate from the database
        exact, next_best, similar = fetch_db_food_matches(ing_name)

        if exact:
            match_name = exact
            match_type = "exact"
            fuzz_score = 100
        elif next_best:
            match_name = next_best
            match_type = "fuzzy"
            match_tuple = next((m for m in similar if m[0] == next_best), None)
            fuzz_score = match_tuple[1] if match_tuple else 80
        else:
            continue  # No match

        match_row = next((f for f in food_entries if f["normalized_name"] == match_name), None)
        if match_row:
            cur.execute("""
                UPDATE ingredients
                SET matched_food_id = ?, match_type = ?, fuzz_score = ?
                WHERE id = ?
            """, (match_row["id"], match_type, fuzz_score, ing_id))
            matched += 1

    conn.commit()
    conn.close()
    print(f"✅ Matched {matched} ingredient(s).")

def main():
    parser = argparse.ArgumentParser(description="Match ingredients to food_info")
    parser.add_argument("--init", action="store_true", help="Recreate the food_info table (destructive)")
    parser.add_argument("--db", default="food_info.db", help="Path to SQLite database")
    args = parser.parse_args()
    match_ingredients(db_path=args.db, init=args.init)

if __name__ == "__main__":
    main()
