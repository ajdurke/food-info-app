import argparse
from recipe_scrapers import scrape_me
from food_project.database.sqlite_connector import save_recipe_and_ingredients

def parse_recipe(url: str) -> dict:
    scraper = scrape_me(url)
    return {
        "title": scraper.title(),
        "ingredients": scraper.ingredients(),
        "instructions": scraper.instructions(),
        "raw_html": scraper.to_json(),  # optional backup
        "url": url
    }

def main():
    parser = argparse.ArgumentParser(description="Scrape a recipe from a URL and save to database")
    parser.add_argument("--url", required=True, help="Recipe URL to scrape")
    parser.add_argument("--db", default="food_info.db", help="Path to SQLite database")
    args = parser.parse_args()

    print(f"🔍 Scraping: {args.url}")
    recipe_data = parse_recipe(args.url)

    print(f"📝 Title: {recipe_data['title']}")
    print(f"🧾 Found {len(recipe_data['ingredients'])} ingredients")
    for ing in recipe_data['ingredients']:
        print(f" - {ing}")

    recipe_id = save_recipe_and_ingredients(recipe_data, db_path=args.db)
    print(f"\n✅ Saved to {args.db} as recipe ID: {recipe_id}")

if __name__ == "__main__":
    main()
