"""Functions for cleaning and parsing raw ingredient text."""

import re
import inflect
from pathlib import Path
from fractions import Fraction
from food_project.processing.units import COMMON_UNITS, extract_unit_size

p = inflect.engine()

FRACTIONS = {
    "½": "1/2", "¼": "1/4", "¾": "3/4", "⅓": "1/3", "⅔": "2/3", "⅛": "1/8"
}

def load_descriptors():
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

def load_descriptor_phrases():
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
    if not text:
        return ""

    for frac, ascii_frac in FRACTIONS.items():
        text = text.replace(frac, ascii_frac)

    text = re.sub(r"\(.*?\)", "", text)

    segments = text.split(",")
    if len(segments[0].split()) >= 2:
        text = segments[0]

    for phrase in DESCRIPTOR_PHRASES:
        text = text.replace(phrase, "")

    text = re.sub(r"\b\d+\s+(and\s+)?\d+/\d+\b", "", text)
    text = re.sub(r"\b\d+/\d+\b", "", text)
    text = re.sub(r"\b\d+(\.\d+)?\b", "", text)

    words = text.lower().split()
    words = [w.strip(",.") for w in words]

    while words and words[-1] in DESCRIPTORS:
        words.pop()

    filtered = []
    for w in words:
        if w in DESCRIPTORS or (p.singular_noun(w) in DESCRIPTORS):
            if len(words) > 1:
                continue
        filtered.append(w)
    words = filtered

    skip_singularization = {"boneless", "skinless", "seedless", "fatless", "skin-on", "bone-in"}
    singular_words = [
        w if w in skip_singularization else p.singular_noun(w) or w
        for w in words
    ]

    return " ".join(singular_words).strip()

def is_countable_item(normalized_name: str) -> bool:
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

def parse_ingredient(raw: str):
    original = raw.strip()

    # Remove fractions and normalize
    for frac, ascii_frac in FRACTIONS.items():
        raw = raw.replace(frac, ascii_frac)

    # Pre-clean multi-quantity formats (e.g., "1/4 cup plus 2 Tbsp")
    raw = re.sub(r"\bor more\b", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\bplus\b", "+", raw, flags=re.IGNORECASE)

    cleaned = raw.lower().replace(" and ", " ")
    cleaned = re.sub(r"\(.*?\)", "", cleaned)
    cleaned = re.sub(r"[^a-zA-Z0-9\s/.\-+]", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Parse compound amounts like "1/4 + 2 tbsp"
    amount = None
    total_amount = 0.0
    compound_parts = re.split(r"\+", cleaned)
    matched_amounts = 0
    unit = None
    final_words = []

    for part in compound_parts:
        part = part.strip()
        match = re.match(
            r'^(\d+\s+\d+/\d+|\d+/\d+|\d+\.\d+|\d+)',
            part
        )
        if match:
            matched_amounts += 1
            num_str = match.group(1)
            try:
                val = float(sum(Fraction(s) for s in num_str.split()))
                total_amount += val
                part = part[len(num_str):].strip()
            except Exception:
                continue

            words = part.split()
            if not unit and words:
                u = words[0]
                if u in COMMON_UNITS or u.rstrip("s") in COMMON_UNITS:
                    unit = u.rstrip("s")
                    words = words[1:]

            final_words.extend(words)

        else:
            final_words.extend(part.split())

    amount = total_amount if matched_amounts else None

    # Remove descriptors from name
    name_words = [w for w in final_words if w not in DESCRIPTORS and p.singular_noun(w) not in DESCRIPTORS]

    normalized_name = normalize_food_name(" ".join(name_words))
    est_grams = extract_unit_size(amount, unit, normalized_name)

    return amount, unit, normalized_name, est_grams
