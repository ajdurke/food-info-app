from recipe_scrapers import scrape_me

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
    url = "https://www.allrecipes.com/recipe/231282/hearty-italian-meatball-soup/"  # or any real recipe URL
    result = parse_recipe(url)

    print(f"\n🍽️ Title: {result['title']}\n")
    print("🧾 Ingredients:")
    for ing in result["ingredients"]:
        print(f" - {ing}")
    
    print("\n📋 Instructions:")
    print(result["instructions"])
