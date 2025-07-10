"""Logic-based checks for ingredient parsing and matching."""

def score_food_match(normalized_name: str, known_foods: list[str]) -> float:
    return 100.0 if normalized_name in known_foods else 60.0

def score_unit(unit: str, known_units: set[str]) -> float:
    return 100.0 if unit in known_units else 50.0
