import argparse
import sqlite3
import os
import sys
from typing import List, Dict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rapidfuzz import process, fuzz

from food_project.database.nutritionix_service import (
    normalize_food_name,
    NUTRITIONIX_APP_ID,
    NUTRITIONIX_API_KEY,
    _fetch_from_api,
)

import requests

SEARCH_URL = "https://trackapi.nutritionix.com/v2/search/instant"


def search_candidates(query: str, limit: int = 5) -> List[str]:
    headers = {
        "x-app-id": NUTRITIONIX_APP_ID,
        "x-app-key": NUTRITIONIX_API_KEY,
    }
    resp = requests.get(SEARCH_URL, params={"query": query}, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    candidates = [item.get("food_name") for item in data.get("common", [])]
    return candidates[:limit]


def init_table(conn: sqlite3.Connection, reset: bool = False) -> None:
    cur = conn.cursor()
    if reset:
        cur.execute("DROP TABLE IF EXISTS food_info")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS food_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_name TEXT NOT NULL,
            normalized_name TEXT NOT NULL UNIQUE,
            match_type TEXT,
            approved INTEGER,
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
        """
    )
    conn.commit()


def insert_food(
    conn: sqlite3.Connection,
    raw_name: str,
    normalized_name: str,
    match_type: str,
    data: Dict[str, float],
    approved: int | None = None,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO food_info (
            raw_name, normalized_name, match_type, approved,
            serving_qty, serving_unit, serving_weight_grams,
            calories, fat, saturated_fat, cholesterol, sodium,
            carbs, fiber, sugars, protein, potassium
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            raw_name,
            normalized_name,
            match_type,
            approved,
            data.get("serving_qty"),
            data.get("serving_unit"),
            data.get("serving_weight_grams"),
            data.get("calories"),
            data.get("fat"),
            data.get("saturated_fat"),
            data.get("cholesterol"),
            data.get("sodium"),
            data.get("carbs"),
            data.get("fiber"),
            data.get("sugars"),
            data.get("protein"),
            data.get("potassium"),
        ),
    )
    conn.commit()


def process_food(name: str, conn: sqlite3.Connection) -> None:
    normalized = normalize_food_name(name)
    cur = conn.cursor()
    cur.execute("SELECT id FROM food_info WHERE normalized_name = ?", (normalized,))
    if cur.fetchone():
        print(f"'{name}' already exists, skipping.")
        return

    try:
        candidates = search_candidates(name)
    except Exception as e:
        print(f"Search failed for '{name}': {e}")
        return

    candidate_map = {normalize_food_name(c): c for c in candidates}

    if normalized in candidate_map:
        api_name = candidate_map[normalized]
        data = _fetch_from_api(api_name)
        insert_food(conn, api_name, normalized, "exact", data, approved=1)
        print(f"Added exact match for '{name}' -> '{api_name}'")
        return

    if not candidates:
        print(f"No candidates for '{name}'")
        return

    best_norm, score = process.extractOne(normalized, list(candidate_map.keys()), scorer=fuzz.ratio)
    best_original = candidate_map[best_norm]
    best_data = _fetch_from_api(best_original)
    insert_food(conn, best_original, best_norm, "best", best_data)
    print(f"Added best match for '{name}' -> '{best_original}' (score {score})")

    for norm, orig in candidate_map.items():
        if norm == best_norm:
            continue
        cur.execute("SELECT id FROM food_info WHERE normalized_name = ?", (norm,))
        if cur.fetchone():
            continue
        try:
            other_data = _fetch_from_api(orig)
        except Exception as e:
            print(f"Failed to fetch '{orig}': {e}")
            continue
        insert_food(conn, orig, norm, "similar", other_data)
        print(f"Added similar match for '{name}' -> '{orig}'")


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate food_info from Nutritionix")
    parser.add_argument("foods", nargs="*", help="Food names to lookup")
    parser.add_argument("--file", help="File containing food names, one per line")
    parser.add_argument("--db", default="food_info.db", help="SQLite database path")
    parser.add_argument("--reset", action="store_true", help="Delete existing food_info table")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    init_table(conn, reset=args.reset)

    foods = list(args.foods)
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            foods.extend([line.strip() for line in f if line.strip()])

    for food in foods:
        process_food(food, conn)

    conn.close()


if __name__ == "__main__":
    main()

