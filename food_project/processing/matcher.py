from rapidfuzz import fuzz
import sqlite3

def fetch_food_matches(normalized_name: str, options: list[str], score_threshold=70, limit=5):
    """
    Return (exact_match, next_best_match, similar_matches_with_scores) from a list of options.
    """
    normalized_name = normalized_name.strip().lower()
    options = [o.strip().lower() for o in options]

    exact_match = normalized_name if normalized_name in options else None
    best_match = None
    best_score = 0
    similar = []

    for option in options:
        score = fuzz.token_sort_ratio(normalized_name, option)
        if score >= score_threshold:
            similar.append((option, score))
            if score > best_score:
                best_score = score
                best_match = option

    return exact_match, best_match if best_match != exact_match else None, similar

def fetch_db_food_matches(ingredient_name: str, db_path="food_info.db"):
    """
    Look up matching food_info entries for a given ingredient name.
    Returns: (exact_match, next_best, similar_matches_with_scores)
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT normalized_name FROM food_info WHERE normalized_name IS NOT NULL")
    all_foods = [row[0] for row in cur.fetchall()]
    conn.close()

    return fetch_food_matches(ingredient_name, all_foods)
