"""CLI to test all steps of the enhanced LLM parsing and nutrition flow."""

import argparse
from food_project.ingestion.parse_recipe_url import parse_recipe
from food_project.llm.full_parser import parse_with_llm
from food_project.llm.estimate_nutrition import estimate_nutrition_from_llm
from food_project.processing.normalization import parse_ingredient

def run_pipeline(url, mock=False):
    print(f"🔗 Fetching recipe: {url}")
    recipe = parse_recipe(url)
    print(f"🧾 Title: {recipe['title']}")
    for step in recipe['ingredients']:
        print(f"➡️ Step: {step}")
        amount, unit, normalized_name, _ = parse_ingredient(step)
        logic_result = {"food": normalized_name, "amount": amount, "unit": unit}

        print(f"🔍 Logic result: {logic_result}")
        llm_result = parse_with_llm(step, mock=mock)
        print(f"🧠 LLM result: {llm_result}")
        if not llm_result.get('food'):
            nutrition_est = estimate_nutrition_from_llm(step, mock=mock)
            print(f"🥣 Estimated nutrition: {nutrition_est}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test LLM parsing pipeline with optional mock mode")
    parser.add_argument("url", help="Recipe URL to parse")
    parser.add_argument("--mock", action="store_true", help="Use mock mode to avoid API/LLM calls")
    args = parser.parse_args()
    run_pipeline(args.url, mock=args.mock)
