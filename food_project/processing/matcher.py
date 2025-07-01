"""Simple fuzzy matching helpers for ingredient names."""

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
        # rapidfuzz returns a similarity score between 0 and 100
        score = fuzz.token_sort_ratio(normalized_name, option)
        if score >= score_threshold:
            similar.append((option, score))
            if score > best_score:
                best_score = score
                best_match = option

    return exact_match, best_match if best_match != exact_match else None, similar

def fetch_db_food_matches(ingredient_name: str, db_path="food_info.db"):
    """Look up possible matches for ``ingredient_name`` in the database."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "SELECT DISTINCT normalized_name FROM food_info WHERE normalized_name IS NOT NULL"
    )
    all_foods = [row[0] for row in cur.fetchall()]
    conn.close()

    # Delegate to ``fetch_food_matches`` which does the fuzzy matching
    return fetch_food_matches(ingredient_name, all_foods)
