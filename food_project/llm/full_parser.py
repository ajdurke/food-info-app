"""LLM fallback parser for ingredient text."""

def parse_with_llm(raw_text: str) -> dict:
    """Call LLM to extract food, amount, unit, and normalized name from raw_text."""
    # Placeholder: Connect to Together API
    return {
        "food": None,
        "amount": None,
        "unit": None,
        "normalized_name": None,
        "food_score": None,
        "unit_score": None,
    }
