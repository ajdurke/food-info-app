"""Functions for cleaning and parsing raw ingredient text."""

import re
import inflect
from food_project.processing.units import COMMON_UNITS, extract_unit_size

p = inflect.engine()  # Library used to convert plural words to singular

DESCRIPTORS = {
    "fresh", "frozen", "dried", "chopped", "sliced", "grated", "minced",
    "shredded", "cooked", "raw", "large", "small", "extra", "extra-virgin",
    "organic", "peeled", "unsalted", "salted", "finely", "coarsely",
    "thinly", "thickly", "trimmed", "melted", "optional", "diagonal"
}

FRACTIONS = {
    "½": "1/2", "¼": "1/4", "¾": "3/4", "⅓": "1/3", "⅔": "2/3", "⅛": "1/8"
}

def normalize_food_name(text):
    """Simplify ingredient text to a consistent, searchable form."""
    if not text:
        return ""
    # Remove things like "(minced)" or trailing descriptions after a comma
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r",.*", "", text)
    words = text.lower().split()
    # Drop descriptive words we don't care about
    words = [w for w in words if w not in DESCRIPTORS]
    # Convert plurals to singular form for easier matching
    singular_words = [p.singular_noun(w) or w for w in words]
    return " ".join(singular_words).strip()

def is_countable_item(normalized_name: str) -> bool:
    """Heuristic check to see if an ingredient is typically counted."""
    countable_keywords = {
        "apple", "banana", "egg", "onion", "lemon", "lime", "orange", "scallion",
        "shallot", "clove", "pepper", "potato", "carrot", "shrimp", "tomato", "zucchini",
        "avocado", "chili", "date", "fig", "radish", "beet", "turnip", "mushroom",
        "meatball", "cookie", "roll", "bun", "patty", "cutlet"
    }
    cleaned = normalized_name.strip().lower()
    return cleaned in countable_keywords or (
        cleaned.endswith("s") and cleaned[:-1] in countable_keywords
    )

def parse_ingredient(text):
    """Break an ingredient string into amount, unit and cleaned name."""
    original = text.strip().lower()

    for symbol, replacement in FRACTIONS.items():
        # Replace unicode fraction characters (½, ¼, etc.) with ascii
        original = original.replace(symbol, replacement)

    original = re.sub(r"\s+", " ", original)

    amount = None
    unit = None
    # Some ingredients mention package sizes like "(16 oz)".  This helper
    # tries to extract the grams from that.
    est_grams = extract_unit_size(original)

    # Look for a numeric amount at the start of the string
    amount_match = re.match(r'^([\d/\.]+)(\s+|$)', original)
    if amount_match:
        try:
            # ``eval`` lets us handle fractions like "1/2"
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