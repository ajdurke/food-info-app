import sqlite3
from fuzzywuzzy import fuzz

DB_PATH = "food_info.db"
FUZZY_THRESHOLD = 75  # you can tweak this

def match_ingredients():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT id, normalized_name FROM food_info")
    food_lookup = cur.fetchall()

    cur.execute("SELECT id, normalized_name FROM ingredients WHERE matched_food_id IS NULL")
    unmatched = cur.fetchall()

    exact = 0
    fuzzy = 0

    for ing_id, norm_ing in unmatched:
        match_id = None
        match_type = None
        best_score = 0

        for food_id, food_norm in food_lookup:
            if norm_ing == food_norm:
                match_id = food_id
                match_type = "exact"
                best_score = 100
                exact += 1
                break
            else:
                score = fuzz.token_sort_ratio(norm_ing, food_norm)
                if score > best_score:
                    best_score = score
                    best_id = food_id

        if not match_id and best_score >= FUZZY_THRESHOLD:
            match_id = best_id
            match_type = "fuzzy"
            fuzzy += 1

        if match_id:
            cur.execute("""
                UPDATE ingredients
                SET matched_food_id = ?, match_type = ?, fuzz_score = ?
                WHERE id = ?
            """, (match_id, match_type, best_score, ing_id))

    conn.commit()
    conn.close()
    print(f"✅ Matched ingredients: {exact} exact, {fuzzy} fuzzy.")

if __name__ == "__main__":
    match_ingredients()
