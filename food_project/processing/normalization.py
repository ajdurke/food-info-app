"""Functions for cleaning and parsing raw ingredient text."""

import re
import inflect
from pathlib import Path
from fractions import Fraction
from food_project.processing.units import COMMON_UNITS, extract_unit_size

p = inflect.engine()  # Library used to convert plural words to singular

FRACTIONS = {
    "½": "1/2", "¼": "1/4", "¾": "3/4", "⅓": "1/3", "⅔": "2/3", "⅛": "1/8"
}

def load_descriptors():
    """Load descriptor words from config/descriptors.txt, ignoring comments and section headers."""
    path = Path(__file__).parent.parent / "config" / "descriptors.txt"
    descriptors = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip().lower()
            if not line or line.startswith("#") or line.startswith("="):
                continue
            descriptors.add(line)
    return descriptors

DESCRIPTORS = load_descriptors()

# Words that should not be singularized (e.g. parsley → parsley)
SKIP_SINGULARIZATION = {
    "parsley", "spinach", "chard", "kale", "lettuce", "rice", "quinoa",
    "arugula", "cilantro", "basil", "chives", "thyme", "rosemary", "mint"
}

def load_descriptor_phrases():
    """Load full multi-word descriptor phrases."""
    path = Path(__file__).parent.parent / "config" / "descriptor_phrases.txt"
    phrases = []
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip().lower()
                if line and not line.startswith("#"):
                    phrases.append(line)
    return phrases

DESCRIPTOR_PHRASES = load_descriptor_phrases()

def normalize_food_name(text):
    """Simplify ingredient text to a consistent, searchable form."""
    if not text:
        return ""

    # Normalize unicode fractions
    for frac, ascii_frac in FRACTIONS.items():
        text = text.replace(frac, ascii_frac)

    # Remove parentheticals and trailing commas
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r",.*", "", text)

    # Remove descriptor phrases first (before splitting into words)
    lowered = text.lower()
    for phrase in DESCRIPTOR_PHRASES:
        lowered = lowered.replace(phrase, "")

    # Remove numbers and fractions
    lowered = re.sub(r"\b\d+\s+(and\s+)?\d+/\d+\b", "", lowered)
    lowered = re.sub(r"\b\d+/\d+\b", "", lowered)
    lowered = re.sub(r"\b\d+(\.\d+)?\b", "", lowered)

    # Tokenize and clean punctuation
    words = lowered.split()
    words = [w.strip(",.") for w in words]

    # Remove trailing descriptors
    while words and words[-1] in DESCRIPTORS:
        words.pop()

    # Remove remaining individual descriptors
    words = [w for w in words if w not in DESCRIPTORS and p.singular_noun(w) not in DESCRIPTORS]


    # Singularize (skip some)
    skip_singularization = {"boneless", "skinless", "seedless", "fatless", "skin-on", "bone-in"}
    singular_words = [
        w if w in skip_singularization else p.singular_noun(w) or w
        for w in words
    ]

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

def parse_amount_v2(text):
    """Parse mixed and fractional numeric quantities like '1 1/2' or '2 and 1/4'."""
    try:
        text = text.lower().replace(" and ", " ")
        parts = text.split()
        total = 0.0
        for part in parts:
            try:
                total += float(Fraction(part))
            except ValueError:
                return None
        return total if total > 0 else None
    except Exception:
        return None

def parse_ingredient(raw: str):
    original = raw.strip()

    # === Step 1: Clean and normalize input ===
    cleaned = original.lower().replace(" and ", " ")  # Handle "1 and 3/4"
    cleaned = re.sub(r"\(.*?\)", "", cleaned)  # remove parentheticals
    cleaned = re.sub(r"[^a-zA-Z0-9\s/.\-¼½¾⅓⅔⅛⅜⅝⅞]", "", cleaned)  # keep basic fractions
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # === Step 2: Extract amount ===
    amount = None
    amount_match = re.match(
        r'^(\d+\s+and\s+\d+/\d+|\d+\s+\d+/\d+|\d+/\d+|\d+\.\d+|\d+[¼½¾⅓⅔⅛⅜⅝⅞]?|\d+)',
        cleaned
    )
    if amount_match:
        amount_str = amount_match.group(1)
        try:
            if " " in amount_str:  # e.g., "1 1/2"
                parts = amount_str.split()
                amount = float(parts[0]) + eval(parts[1])
            elif "/" in amount_str:
                amount = eval(amount_str)
            elif re.search(r"[¼½¾⅓⅔⅛⅜⅝⅞]", amount_str):
                unicodes = {
                    "¼": 0.25, "½": 0.5, "¾": 0.75,
                    "⅓": 1/3, "⅔": 2/3,
                    "⅛": 1/8, "⅜": 3/8, "⅝": 5/8, "⅞": 7/8,
                }
                amount = unicodes.get(amount_str.strip(), None)
            else:
                amount = float(amount_str)
            cleaned = cleaned[len(amount_str):].strip()
        except Exception:
            pass

    # === Step 3: Extract unit ===
    words = cleaned.split()
    words = [w.strip(",.") for w in words]  # strip trailing punctuation before unit check
    unit = None
    if words:
        first = words[0].lower()
        if first in COMMON_UNITS:
            unit = words.pop(0)
        elif first.endswith("s") and first.rstrip("s") in COMMON_UNITS:
            unit = words.pop(0)

    # === Step 4: Normalize the remaining words ===
    normalized_name = normalize_food_name(" ".join(words))
    est_grams = extract_unit_size(amount, unit, normalized_name)

    return amount, unit, normalized_name, est_grams
