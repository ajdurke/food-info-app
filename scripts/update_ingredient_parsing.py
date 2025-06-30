import sqlite3
import re
import sys
import inflect
p = inflect.engine()

DB_PATH = "food_info.db"

# Expanded units including abbreviations
COMMON_UNITS = [
    "cup", "cups", "tbsp", "tablespoon", "tablespoons", "tbsp.", 
    "tsp", "teaspoon", "teaspoons", "tsp.", "oz", "oz.", "ounce", "ounces",
    "lb", "lb.", "pound", "pounds", "gram", "grams", "g", "ml", "liter", "liters",
    "can", "cans", "package", "packages", "pkg", "pkg.", "clove", "cloves", 
    "slice", "slices", "pinch", "dash"
]

DESCRIPTORS = [
    "fresh", "frozen", "dried", "chopped", "sliced", "grated", "minced", 
    "shredded", "cooked", "raw", "large", "small", "extra", "extra-virgin", "organic", "peeled",
    "finely", "coarsely", "thinly", "thickly", "trimmed", "melted", "optional", 
    "diagonal"
]

UNIT_TO_GRAMS = {
    "oz": 28.35, "oz.": 28.35, "ounce": 28.35, "ounces": 28.35,
    "lb": 453.6, "lb.": 453.6, "pound": 453.6, "pounds": 453.6,
    "gram": 1.0, "grams": 1.0, "g": 1.0
}

FRACTIONS = {
    "½": "1/2", "¼": "1/4", "¾": "3/4", "⅓": "1/3", "⅔": "2/3", "⅛": "1/8"
}

def normalize_food_name(text):
    text = re.sub(r"\(.*?\)", "", text)       # remove parentheticals
    text = re.sub(r",.*", "", text)           # remove trailing commas/notes
    words = text.lower().split()
    words = [w for w in words if w not in DESCRIPTORS]
    singular_words = [p.singular_noun(w) or w for w in words]  # singularize
    return " ".join(singular_words).strip()

def extract_unit_size(text):
    match = re.search(r"\((\d+(\.\d+)?)\s*(oz|oz.|ounce|ounces|g|gram|grams|ml|liter|liters)\)", text.lower())
    if match:
        quantity = float(match.group(1))
        unit = match.group(3)
        grams = quantity * UNIT_TO_GRAMS.get(unit, 1.0)
        return grams
    return None

def is_countable_item(normalized_name: str) -> bool:
    # Heuristic list of common countable food items
    countable_keywords = {
        "apple", "banana", "egg", "onion", "lemon", "lime", "orange", "scallion",
        "shallot", "clove", "pepper", "potato", "carrot", "shrimp", "tomato", "zucchini",
        "avocado", "chili", "date", "fig", "radish", "beet", "turnip", "mushroom",
        "meatball", "cookie", "roll", "bun", "patty", "cutlet"
    }

    cleaned = normalized_name.strip().lower()

    # Check both singular and plural form
    if cleaned in countable_keywords:
        return True
    if cleaned.endswith("s") and cleaned[:-1] in countable_keywords:
        return True

    return False

def parse_ingredient(text):
    original = text.strip().lower()

    # Replace unicode fractions
    for symbol, replacement in FRACTIONS.items():
        original = original.replace(symbol, replacement)

    original = re.sub(r"\s+", " ", original)

    amount = None
    unit = None
    est_grams = extract_unit_size(original)

    # Extract amount
    amount_match = re.match(r'^([\d/\.]+)(\s+|$)', original)
    if amount_match:
        try:
            amount = eval(amount_match.group(1))
            original = original[amount_match.end():].strip()
        except:
            pass

    # Extract unit (first word only, must be in known list)
    words = original.split()
    if words and words[0] in COMMON_UNITS:
        unit = words[0]
        words = words[1:]

    # Handle edge case: "juice of 1 lemon"
    if "juice of" in original:
        amount = amount or 1
        unit = "lemon"
        normalized = "lemon juice"
    else:
        normalized = normalize_food_name(" ".join(words))

    # If we have an amount but no unit, and it's probably a countable food
    if amount is not None and unit is None and is_countable_item(normalized):
        unit = "each"

    return amount, unit, normalized, est_grams

def update_ingredients(force=False):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Add new column if needed
    try:
        cur.execute("ALTER TABLE ingredients ADD COLUMN estimated_grams REAL")
    except:
        pass  # already exists

    if force:
        rows = cur.execute("SELECT id, name FROM ingredients").fetchall()
    else:
        rows = cur.execute("SELECT id, name FROM ingredients WHERE normalized_name IS NULL").fetchall()

    updated = 0
    for row in rows:
        ing_id, raw_text = row
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
    force_flag = "--force" in sys.argv
    update_ingredients(force=force_flag)
