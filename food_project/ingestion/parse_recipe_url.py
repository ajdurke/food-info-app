from recipe_scrapers import scrape_me
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from food_project.database.sqlite_connector import save_recipe_and_ingredients



def parse_recipe(url: str) -> dict:
    scraper = scrape_me(url)
    return {
        "title": scraper.title(),
        "ingredients": scraper.ingredients(),
        "instructions": scraper.instructions(),
        "raw_html": scraper.to_json(),  # optional backup
    }

# Example usage
if __name__ == "__main__":
    url = "https://www.foodnetwork.com/recipes/food-network-kitchen/instant-pot-keto-mediterranean-chicken-5500679"
    result = parse_recipe(url)
    result["url"] = url  # Add the URL so it can be saved

    # Save to database
    recipe_id = save_recipe_and_ingredients(result)

    # Confirm
    print(f"\n✅ Saved recipe '{result['title']}' (ID: {recipe_id}) with {len(result['ingredients'])} ingredients.\n")

    print("🧾 Ingredients:")
    for ing in result["ingredients"]:
        print(f" - {ing}")

    print("\n📋 Instructions:")
    print(result["instructions"])

