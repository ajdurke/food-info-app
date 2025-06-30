import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sqlite3
from typing import List
from food_project.database.sqlite_connector import get_connection, init_db
from food_project.database.nutritionix_service import fetch_food_matches

# ==== CONFIGURATION ====
DELETE_EXISTING = True  # Set to False to keep existing food_info data
FOOD_LIST_FILE = "scripts/foods.txt"  # Path to file with food names (one per line)
# ========================

def clear_existing_data(conn):
    with conn:
        conn.execute("DELETE FROM food_info")
        print("Cleared existing food_info data.")

def read_food_list(path: str) -> List[str]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Food list file not found: {path}")
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def already_exists(conn, normalized_name):
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM food_info WHERE normalized_name = ?", (normalized_name,))
    return cursor.fetchone() is not None

def insert_entry(conn, food_data, match_type, approved=None):
    food_data["match_type"] = match_type
    food_data["approved"] = approved
    with conn:
        conn.execute("""
            INSERT INTO food_info (
                raw_name, normalized_name, serving_qty, serving_unit,
                serving_weight_grams, calories, fat, saturated_fat, cholesterol,
                sodium, carbs, fiber, sugars, protein, potassium, match_type, approved
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            food_data.get("raw_name"),
            food_data.get("normalized_name"),
            food_data.get("serving_qty"),
            food_data.get("serving_unit"),
            food_data.get("serving_weight_grams"),
            food_data.get("calories"),
            food_data.get("fat"),
            food_data.get("saturated_fat"),
            food_data.get("cholesterol"),
            food_data.get("sodium"),
            food_data.get("carbs"),
            food_data.get("fiber"),
            food_data.get("sugars"),
            food_data.get("protein"),
            food_data.get("potassium"),
            match_type,
            approved
        ))

def run():
    conn = get_connection()
    init_db(conn)

    if DELETE_EXISTING:
        clear_existing_data(conn)

    food_names = read_food_list(FOOD_LIST_FILE)

    for food_name in food_names:
        print(f"\n Fetching matches for: {food_name}")
        exact, next_best, others = fetch_food_matches(food_name)

        if exact and not already_exists(conn, exact["normalized_name"]):
            insert_entry(conn, exact, match_type="exact", approved=1)
            print("Inserted exact match")

        if next_best and not already_exists(conn, next_best["normalized_name"]):
            insert_entry(conn, next_best, match_type="best", approved=None)
            print("Inserted next best match (pending review)")

        for alt in others:
            if not already_exists(conn, alt["normalized_name"]):
                insert_entry(conn, alt, match_type="similar", approved=None)
                print("Inserted similar match (pending review)")

    conn.close()
    print("\n Done populating food_info.")

if __name__ == "__main__":
    run()
