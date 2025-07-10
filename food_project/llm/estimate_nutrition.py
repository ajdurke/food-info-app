"""LLM fallback for estimating nutrition when API fails."""

def estimate_nutrition_from_llm(text: str, mock=False) -> dict:
    if mock:
        return {
            "calories": 200,
            "protein": 10,
            "fat": 5,
            "carbs": 15,
        }

    # TODO: Add real logic later
    return {
        "calories": 123,
        "protein": 4,
        "fat": 9,
        "carbs": 12,
    }

