import argparse
import os
from pathlib import Path
from food_project.database.sqlite_connector import get_connection, init_db
from food_project.database.nutritionix_service import get_nutrition_data

DEFAULT_FILE = "scripts/foods.txt"
MAX_API_CALLS = 200

def clear_existing_data(conn):
    with conn:
        conn.execute("DELETE FROM food_info")
        print("🧹 Cleared existing food_info data.")

def read_food_list(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ Food list file not found: {path}")
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def fetch_and_insert(conn, food_name) -> bool:
    print(f"🔍 Fetching data for: {food_name}")
    food_data = get_nutrition_data(food_name, conn)
    if not food_data:
        print(f"❌ No data found for: {food_name}")
        return False
    print(f"✅ Inserted or retrieved: {food_data['normalized_name']}")
    return True

    print(f"✅ Inserted: {food_data['normalized_name']}")
    return True

def main():
    print("🧪 Script is running...")
    parser = argparse.ArgumentParser(description="Populate food_info from Nutritionix")
    parser.add_argument("--food", help="Fetch a single food item by name")
    parser.add_argument("--file", default=DEFAULT_FILE, help="Path to foods.txt")
    parser.add_argument("--clear", action="store_true", help="Delete existing food_info entries")
    parser.add_argument("--max", type=int, default=MAX_API_CALLS, help="Max API calls to use")
    parser.add_argument("--db", default="food_info.db", help="Path to SQLite database")

    args = parser.parse_args()
    db_path = Path(args.db)

    conn = get_connection(db_path)
    init_db(conn)

    if args.clear:
        clear_existing_data(conn)

    if args.food:
        fetch_and_insert(conn, args.food)
    else:
        food_names = read_food_list(args.file)
        used = 0
        for food_name in food_names:
            if used >= args.max:
                print("🔁 Reached API limit.")
                break
            if fetch_and_insert(conn, food_name):
                used += 1

        print(f"🎉 Finished. {used} food(s) inserted.")

    conn.close()

if __name__ == "__main__":
    main()

