
import sqlite3
import re
import sys

DB_PATH = "food_info.db"

# Common units to match against
COMMON_UNITS = [
    "cup", "cups", "tbsp", "tablespoon", "tablespoons",
    "tsp", "teaspoon", "teaspoons", "oz", "ounce", "ounces",
    "pound", "pounds", "gram", "grams", "g", "ml", "liter", "liters",
    "can", "cans", "package", "packages", "clove", "cloves", "slice", "slices", "pinch"
]

DESCRIPTORS = [
    "fresh", "frozen", "dried", "chopped", "sliced", "grated", "minced", 
    "shredded", "cooked", "raw", "large", "small", "extra", "organic", "peeled"
]

# Simple mapping of units to grams (can expand or customize per food later)
UNIT_TO_GRAMS = {
    "ounce": 28.35,
    "ounces": 28.35,
    "oz": 28.35,
    "pound": 453.6,
    "pounds": 453.6,
    "gram": 1.0,
    "grams": 1.0,
    "g": 1.0
}

def normalize_food_name(text):
    # Remove parentheses, commas, and trailing notes
    text = re.sub(r"\(.*?\)", "", text)  # remove (14 ounce) style
    text = re.sub(r",.*$", "", text)  # remove ", divided", ", undrained"
    words = text.lower().split()
    words = [w for w in words if w not in DESCRIPTORS]
    return " ".join(words).strip()

def extract_unit_size(text):
    match = re.search(r"\((\d+(\.\d+)?)[\s\-]*(oz|ounce|ounces|g|gram|grams|ml|liter|liters)\)", text.lower())
    if match:
        quantity = float(match.group(1))
        unit = match.group(3)
        grams = quantity * UNIT_TO_GRAMS.get(unit, 1.0)
        return grams
    return None

def parse_ingredient(text):
    original_text = text.strip().lower()
    text = original_text

    # Replace common unicode fractions
    text = text.replace("½", "1/2").replace("¼", "1/4").replace("¾", "3/4")

    amount = None
    unit = None
    est_grams = extract_unit_size(text)

    # Extract amount
    amount_match = re.match(r'^([\d\.\/]+)(\s+|$)', text)
    if amount_match:
        try:
            amount = eval(amount_match.group(1))
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
    return amount, unit, normalized_name, est_grams

def update_ingredients(force=False):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Add column if missing
    try:
        cur.execute("ALTER TABLE ingredients ADD COLUMN estimated_grams REAL")
    except:
        pass  # already exists

    if force:
        rows = cur.execute("SELECT id, name FROM ingredients").fetchall()
    else:
        rows = cur.execute("SELECT id, name FROM ingredients WHERE normalized_name IS NULL").fetchall()

    for row in rows:
        ing_id, raw_text = row
        amount, unit, normalized_name, est_grams = parse_ingredient(raw_text)
        cur.execute("""
            UPDATE ingredients
            SET amount = ?, unit = ?, normalized_name = ?, estimated_grams = ?
            WHERE id = ?
        """, (amount, unit, normalized_name, est_grams, ing_id))

    conn.commit()
    conn.close()
    print(f"✅ Updated {len(rows)} ingredient(s). {'(forced)' if force else '(new only)'}")

if __name__ == "__main__":
    force_flag = "--force" in sys.argv
    update_ingredients(force=force_flag)
