"""LLM fallback for estimating nutrition when API fails."""

def estimate_nutrition_from_llm(raw_text: str) -> dict:
    """Return dictionary with estimated nutrition fields."""
    # Placeholder: Connect to Together API
    return {
        "calories": None,
        "fat": None,
        "protein": None,
        "carbs": None,
        "fiber": None,
        "sodium": None,
        "potassium": None,
    }
