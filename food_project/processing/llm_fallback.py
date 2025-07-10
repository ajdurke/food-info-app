"""LLM fallback logic for ingredient normalization and matching."""

import json
import os
from food_project.processing.together_client import call_together_ai



def call_llm(raw_text: str, current_name: str) -> dict:
    """
    Calls a Together.ai LLM to clean and interpret ingredient text.

    Args:
        raw_text: Full ingredient text from the recipe
        current_name: Pre-parsed normalized name (to provide context)

    Returns:
        Dictionary with keys: food, amount, unit, normalized_name, food_score, unit_score
    """
    prompt = (
        "You are a helpful assistant that extracts structured data from messy recipe ingredients.\n"
        "Here is the raw text of a recipe step: '{raw_text}'\n"
        "The currently parsed ingredient name is: '{current_name}'\n"
        "Return a JSON object with fields: food, amount, unit, normalized_name, food_score, unit_score.\n"
        "If multiple interpretations exist (e.g. fresh or dried herbs), return the most general/common one.\n"
        "Example output: {\"food\": \"thyme\", \"amount\": 1.5, \"unit\": \"teaspoon\", "
        "\"normalized_name\": \"thyme\", \"food_score\": 0.9, \"unit_score\": 1.0}"
    ).format(raw_text=raw_text, current_name=current_name)

    try:
        response = call_together_ai(prompt)
        content = response.strip()

        # Remove extra wrapping or accidental multi-JSON output
        start = content.find("{")
        end = content.rfind("}") + 1
        content = content[start:end]

        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else None
    except Exception as e:
        print(f"❌ JSON parsing failed: {e}")
        print(f"🔎 Raw text that failed to parse: {repr(content)}")
        return None
