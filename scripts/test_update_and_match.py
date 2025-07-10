import sys
from pathlib import Path
import argparse
import sqlite3
import pandas as pd

# Add project root to Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from food_project.processing.ingredient_updater import update_ingredients
from food_project.ingestion.match_ingredients_to_food_info import match_ingredients

def main():
    parser = argparse.ArgumentParser(description="Test full ingredient update and match flow")
    parser.add_argument("--db", default="food_info.db", help="Path to SQLite database")
    parser.add_argument("--mock", action="store_true", help="Use mock LLM and API responses")
    parser.add_argument("--mode", choices=["auto", "match", "full"], default="auto", help="Update mode to use")
    args = parser.parse_args()

    db_path = Path(args.db)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    print("\n🔍 BEFORE:")
    before_df = pd.read_sql_query(
        "SELECT id, recipe_id, food_name, normalized_name, matched_food_id FROM ingredients WHERE normalized_name IS NULL OR matched_food_id IS NULL",
        conn
    )
    print(before_df)

    print(f"\n⚙️ Running update_ingredients(mode='{args.mode}')...")
    update_ingredients(mode=args.mode, db_path=args.db, mock=args.mock)

    print("\n⚙️ Running match_ingredients()...")
    match_ingredients()

    print("\n🔍 AFTER:")
    after_df = pd.read_sql_query(
        "SELECT id, recipe_id, food_name, normalized_name, matched_food_id FROM ingredients WHERE normalized_name IS NULL OR matched_food_id IS NULL",
        conn
    )
    print(after_df)

    conn.close()

if __name__ == "__main__":
    main()
