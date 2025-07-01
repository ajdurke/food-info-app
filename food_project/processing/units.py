"""Utility constants and helpers for unit conversion."""

import re

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

def extract_unit_size(text):
    """Extract the number of grams from strings like "(16 oz)"."""
    match = re.search(r"\((\d+(\.\d+)?)\s*(oz|oz.|ounce|ounces|g|gram|grams|ml|liter|liters)\)", text.lower())
    if match:
        quantity = float(match.group(1))
        unit = match.group(3)
        grams = quantity * UNIT_TO_GRAMS.get(unit, 1.0)
        return grams
    # No size information found
    return None