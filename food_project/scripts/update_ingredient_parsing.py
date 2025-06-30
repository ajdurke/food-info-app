import sqlite3
import re
import sys
from food_project.utils.normalization import normalize_food_name
import inflect

p = inflect.engine()
DB_PATH = "food_info.db"

COMMON_UNITS = [
    "cup", "cups", "tbsp", "tablespoon", "tablespoons", "tbsp.",
    "tsp", "teaspoon", "teaspoons", "tsp.", "oz", "oz.", "ounce", "ounces",
    "lb", "lb.", "pound", "pounds", "gram", "grams", "g", "ml", "liter", "liters",
    "can", "cans", "package", "packages", "pkg", "pkg.", "clove", "cloves",
    "slice", "slices", "pinch", "dash"
]

UNIT_TO_GRAMS = {
    "oz": 28.35, "oz.": 28.35, "ounce": 28.35, "ounces": 28.35,
    "lb": 453.6, "lb.": 453.6, "pound": 453.6, "pounds": 453.6,
    "gram": 1.0, "grams": 1.0, "g": 1.0
}

FRACTIONS = {
    "½": "1/2", "¼": "1/4", "¾": "3/4", "⅓": "1/3", "⅔": "2/3", "⅛": "1/8"
}

def extract_unit_size(text):
    match = re.search(r"\((\d+(\.\d+)?)\s*(oz|oz.|ounce|ounces|g|gram|grams|ml|liter|liters)\)", text.lower())
    if match:
        quantity = float(match.group(1))
        unit = match.group(3)
        grams = quantity * UNIT_TO_GRAMS.get(unit, 1.0)
        return grams
    return None

def is_countable_item(normalized_name: str) -> bool:
    countable_keywords = {
        "apple", "banana", "egg", "onion", "lemon", "lime", "orange", "scallion",
        "shallot", "clove", "pepper", "potato", "carrot", "shrimp", "tomato", "zucchini",
        "avocado", "chili", "date", "fig", "radish", "beet", "turnip", "mushroom",
        "meatball", "cookie", "roll", "bun", "patty", "cutlet"
    }
    cleaned = normalized_name.strip().lower()
    return cleaned in countable_keywords or (cleaned.endswith("s") and cleaned[:-1] in countable_keywords)

def parse_ingredient(text):
    original = text.strip().lower()

    for symbol, replacement in FRACTIONS.items():
        original = original.replace(symbol, replacement)

    original = re.sub(r"\s+", " ", original)

    amount = None
    unit = None
    est_grams = extract_unit_size(original)

    amount_match = re.match(r'^([\d/\.]+)(\s+|$)', original)
    if amount_match:
        try:
            amount = eval(amount_match.group(1))
            original = original[amount_match.end():].strip()
        except:
            pass

    words = original.split()
    if words and words[0] in COMMON_UNITS:
        unit = words[0]
        words = words[1:]

    if "juice of" in original:
        amount = amount or 1
        unit = "lemon"
        normalized = "lemon juice"
    else:
        normalized = normalize_food_name(" ".join(words))

    if amount is not None and unit is None and is_countable_item(normalized):
        unit = "each"

    return amount, unit, normalized, est_grams

def update_ingredients(force=False):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute("ALTER TABLE ingredients ADD COLUMN estimated_grams REAL")
    except: pass
    try:
        cur.execute("ALTER TABLE ingredients ADD COLUMN fuzz_score REAL")
    except: pass

    rows = cur.execute("SELECT id, name FROM ingredients" + ("" if force else " WHERE normalized_name IS NULL")).fetchall()

    updated = 0
    for ing_id, raw_text in rows:
        amount, unit, normalized_name, est_grams = parse_ingredient(raw_text)
        cur.execute("""
            UPDATE ingredients
            SET amount = ?, unit = ?, normalized_name = ?, estimated_grams = ?
            WHERE id = ?
        """, (amount, unit, normalized_name, est_grams, ing_id))
        updated += 1

    conn.commit()
    conn.close()
    print(f"✅ Updated {updated} ingredient(s). {'(forced)' if force else '(new only)'}")

if __name__ == "__main__":
    update_ingredients(force="--force" in sys.argv)
