"""Utility constants and helpers for unit conversion."""

import re

COMMON_UNITS = [
    "cup", "cups", "tbsp", "tablespoon", "tablespoons", "tbsp.",
    "tsp", "teaspoon", "teaspoons", "tsp.", "oz", "oz.", "ounce", "ounces",
    "lb", "lb.", "pound", "pounds", "gram", "grams", "g", "ml", "liter", "liters",
    "can", "cans", "package", "packages", "pkg", "pkg.", "clove", "cloves",
    "slice", "slices", "pinch", "sprig", "sprigs", "bunch", "package", "bag",
    "stick", "recipe", "sheet", "pint", "jar", "stalk", "ear", "ears", "cube",
    "strip", "chunk", "dash", "piece", "drop",
]

UNIT_TO_GRAMS = {
    "oz": 28.35, "oz.": 28.35, "ounce": 28.35, "ounces": 28.35,
    "lb": 453.6, "lb.": 453.6, "pound": 453.6, "pounds": 453.6,
    "gram": 1.0, "grams": 1.0, "g": 1.0
}

import re

def extract_unit_size(amount, unit, normalized_name):
    """Placeholder function to estimate grams based on amount, unit, and food name."""
    return None  # Real logic will go here later

