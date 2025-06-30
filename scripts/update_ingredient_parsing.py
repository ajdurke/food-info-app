
import sqlite3
import re
import sys

DB_PATH = "food_info.db"

COMMON_UNITS = [
    "cup", "cups", "tbsp", "tablespoon", "tablespoons",
    "tsp", "teaspoon", "teaspoons", "oz", "ounce", "ounces",
    "pound", "pounds", "gram", "grams", "ml", "liter", "liters",
    "can", "cans", "package", "packages", "clove", "cloves", "slice", "slices", "pinch"
]

DESCRIPTORS = [
    "fresh", "frozen", "dried", "chopped", "sliced", "grated", "minced", 
    "shredded", "cooked", "raw", "large", "small", "extra", "organic", "peeled"
]

def normalize_food_name(text):
    words = text.lower().split()
    words = [w for w in words if w not in DESCRIPTORS]
    return " ".join(words)

def parse_ingredient(text):
    text = text.strip().lower()
    # Replace unicode fractions
    fraction_map = {"½": "1/2", "¼": "1/4", "¾": "3/4"}
    for symbol, replacement in fraction_map.items():
        text = text.replace(symbol, replacement)

    amount = None
    unit = None

    # Extract amount
    amount_match = re.match(r'^([\d\.\/]+)(\s+|$)', text)
    if amount_match:
        amount_str = amount_match.group(1)
        try:
            amount = eval(amount_str)
            text = text[amount_match.end():].strip()
        except:
            pass

    # Extract unit as a full word
    words = text.split()
    if words and words[0] in COMMON_UNITS:
        unit = words[0]
        words = words[1:]

    ingredient_name = " ".join(words)
    normalized_name = normalize_food_name(ingredient_name)
    return amount, unit, normalized_name

def update_ingredients(force=False):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if force:
        rows = cur.execute("SELECT id, name FROM ingredients").fetchall()
    else:
        rows = cur.execute("SELECT id, name FROM ingredients WHERE normalized_name IS NULL").fetchall()

    for row in rows:
        ing_id, raw_text = row
        amount, unit, normalized_name = parse_ingredient(raw_text)
        cur.execute("""
            UPDATE ingredients
            SET amount = ?, unit = ?, normalized_name = ?
            WHERE id = ?
        """, (amount, unit, normalized_name, ing_id))

    conn.commit()
    conn.close()
    print(f"✅ Updated {len(rows)} ingredient(s). {'(forced)' if force else '(new only)'}")

if __name__ == "__main__":
    force_flag = "--force" in sys.argv
    update_ingredients(force=force_flag)
