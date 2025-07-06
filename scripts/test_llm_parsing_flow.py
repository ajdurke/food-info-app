"""CLI to test all steps of the enhanced LLM parsing and nutrition flow."""

from food_project.ingestion.parse_recipe_url import parse_recipe
from food_project.processing.ingredient_updater import update_ingredients
from food_project.processing.matcher import fetch_db_food_matches
from food_project.llm.full_parser import parse_with_llm
from food_project.llm.estimate_nutrition import estimate_nutrition_from_llm

def run_pipeline(url):
    print(f"🔗 Fetching recipe: {url}")
    recipe = parse_recipe(url)
    print(f"🧾 Title: {recipe['title']}")
    for step in recipe['ingredients']:
        print(f"➡️ Step: {step}")
        # Logic parse would go here (placeholder)
        logic_result = {"food": "?", "amount": "?", "unit": "?"}
        print(f"🔍 Logic result: {logic_result}")
        llm_result = parse_with_llm(step)
        print(f"🧠 LLM result: {llm_result}")
        if not llm_result['food']:
            nutrition_est = estimate_nutrition_from_llm(step)
            print(f"🥣 Estimated nutrition: {nutrition_est}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.test_llm_parsing_flow.py <recipe_url>")
    else:
        run_pipeline(sys.argv[1])
