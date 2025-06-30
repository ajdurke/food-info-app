import sqlite3
from rapidfuzz import fuzz
from food_project.utils.normalization import normalize_food_name

DB_PATH = "food_info.db"

def match_ingredients():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    conn.row_factory = sqlite3.Row

    # Add column for fuzz_score if not exists
    try:
        cur.execute("ALTER TABLE ingredients ADD COLUMN fuzz_score REAL")
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
        ing_id, ing_name = ing
        if not ing_name:
            continue

        # Check for exact match first
        exact = next((f for f in food_entries if f["normalized_name"] == ing_name), None)
        if exact:
            cur.execute("""
                UPDATE ingredients
                SET matched_food_id = ?, match_type = ?, fuzz_score = ?
                WHERE id = ?
            """, (exact["id"], "exact", 100, ing_id))
            total += 1
            continue

        # Otherwise, try fuzzy matching
        best_match = None
        best_score = 0
        for food in food_entries:
            score = fuzz.token_sort_ratio(ing_name, food["normalized_name"])
            if score > best_score:
                best_score = score
                best_match = food

        if best_match and best_score >= 85:
            cur.execute("""
                UPDATE ingredients
                SET matched_food_id = ?, match_type = ?, fuzz_score = ?
                WHERE id = ?
            """, (best_match["id"], "fuzzy", best_score, ing_id))
            total += 1

    conn.commit()
    conn.close()
    print(f"✅ Matched {total} ingredient(s).")

if __name__ == "__main__":
    match_ingredients()
