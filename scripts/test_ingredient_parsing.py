from food_project.processing.normalization import parse_ingredient
from food_project.database.sqlite_connector import get_connection
from pathlib import Path

def test_parsing(db_path="food_info.db"):
    conn = get_connection(Path(db_path))
    cur = conn.cursor()
    rows = cur.execute("SELECT id, food_name FROM ingredients").fetchall()

    print("\n🔍 Full Ingredient Parsing Test:\n")

    for row in rows:
        raw = row["food_name"]
        amount, unit, normalized, grams = parse_ingredient(raw)

        show = (normalized != raw.strip().lower())

        if show:
            print(f"[{row['id']}] {raw}")
            print(f"     → amount: {amount}, unit: {unit}, normalized: {normalized}, est_grams: {grams}\n")


if __name__ == "__main__":
    test_parsing()
