print("✅ ingredient_updater.py loaded")

"""Parse raw ingredient text and store structured info, with LLM fallback and nutrition enrichment."""

import sqlite3
import argparse

from food_project.processing.normalization import parse_ingredient
from food_project.processing.validator import score_food_match, score_unit
from food_project.processing.units import COMMON_UNITS
from food_project.llm.full_parser import parse_with_llm
from food_project.llm.estimate_nutrition import estimate_nutrition_from_llm
from food_project.database.nutritionix_service import get_nutrition_data
from food_project.database.sqlite_connector import init_db

def update_ingredients(force=False, db_path="food_info.db", init=False, mock=False):
    """Update ingredients table with parsed amounts, units, match scores, LLM fallback, and nutrition."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if init:
        print("⚙️ init_db() is recreating the food_info table")
        init_db(conn)

    # Ensure review log table exists
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ingredient_review_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ingredient_id INTEGER,
        raw_text TEXT,
        normalized_name TEXT,
        amount REAL,
        unit TEXT,
        food_score REAL,
        unit_score REAL,
        used_llm INTEGER,
        used_llm_estimate INTEGER,
        used_nutritionix INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        approved TEXT DEFAULT 'pending'
    )
    """)

    try:
        cur.execute("SELECT COUNT(*) FROM ingredients")
    except sqlite3.OperationalError:
        print("❌ Error: ingredients table missing. Did you initialize the DB?")
        conn.close()
        return

    total = cur.fetchone()[0]
    print(f"📊 Total ingredients in DB: {total}")

    for column_def in [
        "ALTER TABLE ingredients ADD COLUMN amount REAL",
        "ALTER TABLE ingredients ADD COLUMN unit TEXT",
        "ALTER TABLE ingredients ADD COLUMN normalized_name TEXT",
        "ALTER TABLE ingredients ADD COLUMN estimated_grams REAL",
        "ALTER TABLE ingredients ADD COLUMN fuzz_score REAL",
        "ALTER TABLE ingredients ADD COLUMN food_score REAL",
        "ALTER TABLE ingredients ADD COLUMN unit_score REAL",
        "ALTER TABLE ingredients ADD COLUMN matched_food_id INTEGER"
    ]:
        try:
            cur.execute(column_def)
        except sqlite3.OperationalError:
            pass

    cur.execute("SELECT id, normalized_name FROM food_info")
    food_info_rows = cur.fetchall()
    known_foods = [row["normalized_name"] for row in food_info_rows]
    food_name_to_id = {row["normalized_name"]: row["id"] for row in food_info_rows}

    if not force:
        query = "SELECT id, food_name FROM ingredients WHERE normalized_name IS NULL"
    else:
        query = "SELECT id, food_name FROM ingredients WHERE normalized_name IS NOT NULL AND matched_food_id IS NULL"

    rows = cur.execute(query).fetchall()
    print(f"🔍 Ingredients to update: {len(rows)}")

    updated = 0
    for ing_id, raw_text in rows:
        used_llm = 0
        used_llm_estimate = 0
        used_nutritionix = 0

        amount, unit, normalized_name, est_grams = parse_ingredient(raw_text)
        food_score = score_food_match(normalized_name, known_foods)
        unit_score = score_unit(unit, set(COMMON_UNITS))

        if (food_score < 80 or unit_score < 80) and raw_text:
            used_llm = 1
            print(f"🤖 Using LLM for ingredient {ing_id}: '{raw_text}' (scores: food={food_score}, unit={unit_score})")
            llm_result = parse_with_llm(raw_text, mock=mock)
            if llm_result.get("food"):
                amount = llm_result.get("amount")
                unit = llm_result.get("unit")
                normalized_name = llm_result.get("normalized_name")
                est_grams = None
                food_score = llm_result.get("food_score", 60.0)
                unit_score = llm_result.get("unit_score", 60.0)

        matched_food_id = food_name_to_id.get(normalized_name)
        result = None
        if not matched_food_id and normalized_name:
            print(f"🥣 Fetching nutrition info for: {normalized_name}")
            result = get_nutrition_data(normalized_name, conn, use_mock=mock, skip_if_exists=True)
            used_nutritionix = 1 if result else 0

            if not result:
                used_llm_estimate = 1
                print(f"⚠️ API failed. Estimating nutrition via LLM for: {normalized_name}")
                est = estimate_nutrition_from_llm(normalized_name, mock=mock)
                if est:
                    cur.execute("""
                        INSERT INTO food_info (
                            raw_name, normalized_name, serving_qty, serving_unit,
                            serving_weight_grams, calories, fat, saturated_fat, cholesterol,
                            sodium, carbs, fiber, sugars, protein, potassium,
                            match_type, approved
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        normalized_name, normalized_name,
                        100, "g", 100,
                        est.get("calories"), est.get("fat"), est.get("saturated_fat"), est.get("cholesterol"),
                        est.get("sodium"), est.get("carbs"), est.get("fiber"), est.get("sugars"),
                        est.get("protein"), est.get("potassium"),
                        "llm_estimate", 0
                    ))
                    conn.commit()

            cur.execute("SELECT id FROM food_info WHERE normalized_name = ?", (normalized_name,))
            row = cur.fetchone()
            matched_food_id = row["id"] if row else None

        cur.execute("""
            UPDATE ingredients
            SET amount = ?, unit = ?, normalized_name = ?, estimated_grams = ?,
                food_score = ?, unit_score = ?, matched_food_id = ?
            WHERE id = ?
        """, (
            amount, unit, normalized_name, est_grams,
            food_score, unit_score, matched_food_id,
            ing_id
        ))
        updated += 1

        # Log this update
        cur.execute("""
            INSERT INTO ingredient_review_log (
                ingredient_id, raw_text, normalized_name, amount, unit,
                food_score, unit_score,
                used_llm, used_llm_estimate, used_nutritionix
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ing_id, raw_text, normalized_name, amount, unit,
            food_score, unit_score,
            used_llm, used_llm_estimate, used_nutritionix
        ))

    conn.commit()

    if updated:
        cur.execute("""
            SELECT food_name, normalized_name, amount, unit, food_score, unit_score
            FROM ingredients
            ORDER BY id DESC
            LIMIT 3
        """)
        print("🧾 Example updates:")
        for row in cur.fetchall():
            print(" -", tuple(row))

    conn.close()
    print(f"✅ Updated {updated} ingredient(s). {'(forced)' if force else '(new only)'}")

def main():
    parser = argparse.ArgumentParser(description="Update parsed ingredient data")
    parser.add_argument("--init", action="store_true", help="Recreate food_info table before running (destructive)")
    parser.add_argument("--db", default="food_info.db", help="Path to SQLite database")
    parser.add_argument("--force", action="store_true", help="Force reprocessing of all ingredients")
    parser.add_argument("--mock", action="store_true", help="Use mock LLM and API responses")
    args = parser.parse_args()

    update_ingredients(
        force=args.force,
        db_path=args.db,
        init=args.init,
        mock=args.mock
    )

# Only run main() if executed as script
if __name__ == "__main__":
    main()

