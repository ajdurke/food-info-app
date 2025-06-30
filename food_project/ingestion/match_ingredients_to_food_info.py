import sqlite3
from food_project.processing.matcher import fetch_db_food_matches
from food_project.processing.normalization import normalize_food_name

DB_PATH = "food_info.db"

def match_ingredients():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Add required columns if not already present
    try:
        cur.execute("ALTER TABLE ingredients ADD COLUMN fuzz_score REAL")
    except:
        pass
    try:
        cur.execute("ALTER TABLE ingredients ADD COLUMN match_type TEXT")
    except:
        pass
    try:
        cur.execute("ALTER TABLE ingredients ADD COLUMN matched_food_id INTEGER")
    except:
        pass

    ingredients = cur.execute("""
        SELECT id, normalized_name FROM ingredients
        WHERE matched_food_id IS NULL
    """).fetchall()

    food_entries = cur.execute("""
        SELECT id, normalized_name FROM food_info
    """).fetchall()

    total = 0
    for ing in ingredients:
        ing_id, ing_name = ing["id"], ing["normalized_name"]
        if not ing_name:
            continue

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
            continue  # no match found

        match_row = next((f for f in food_entries if f["normalized_name"] == match_name), None)
        if match_row:
            cur.execute("""
                UPDATE ingredients
                SET matched_food_id = ?, match_type = ?, fuzz_score = ?
                WHERE id = ?
            """, (match_row["id"], match_type, fuzz_score, ing_id))
            total += 1

    conn.commit()
    conn.close()
    print(f"✅ Matched {total} ingredient(s).")

if __name__ == "__main__":
    match_ingredients()
