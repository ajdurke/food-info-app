# Food Info App

The value proposition of the app is that there are nutritional, environmental, and cost trade offs to different recipes / foods. This information is known, but it's never shown aggregated in one place so that the user can make an informed decision. 

Therefore, the entire app revolves around a couple key capabilities:

- The ability to match the food items across different sources / formats. This likely includes regular maintenance and manual approvals
- the ability to quickly and flexibly visualize different options to the user and their implications



## Database Schema

This project originally stored data in Google Sheets, but it isn't used any more because we migrated to an SQLite backend.

The SQLite database uses 3 main tables instead of repeating recipe information for every ingredient:

```
# Table: food_info
#
# Columns:
# - id (INTEGER, PRIMARY KEY): Unique identifier for the food entry
# - raw_name (TEXT, NOT NULL): I don't know whether this is the original name returned from API or the name submitted tot he API for querying (e.g. "Red Chile Pepper")
# - normalized_name (TEXT, NOT NULL): Cleaned and token-normalized name (e.g. "chile")
# - serving_qty (TEXT, nullable): Serving quantity (e.g. "1", "100", etc.)
# - serving_unit (TEXT, nullable): Unit associated with serving size (e.g. "g", "cup", "tsp")
# - serving_weight_grams (REAL, nullable): Serving weight in grams
# - calories (REAL, nullable): Calories per serving
# - fat (REAL, nullable): Total fat in grams
# - saturated_fat (REAL, nullable): Saturated fat in grams
# - cholesterol (REAL, nullable): Cholesterol in milligrams
# - sodium (REAL, nullable): Sodium in milligrams
# - carbs (REAL, nullable): Total carbohydrates in grams
# - fiber (REAL, nullable): Dietary fiber in grams
# - sugars (REAL, nullable): Total sugar in grams
# - protein (REAL, nullable): Protein in grams
# - potassium (REAL, nullable): Potassium in milligrams
# - match_type (TEXT, nullable): I think (not sure) that this is the match status from the raw_name to the normalized_name (e.g. "exact", "fuzzy", "manual_fake")
# - approved (INTEGER, nullable): Whether the row was manually approved (1 = yes, 0 = no)


# Table: ingredients
#
# Columns:
# - id (INTEGER, PRIMARY KEY): Unique identifier
# - recipe_id (INTEGER, NOT NULL): Foreign key to the recipes table
# - food_name (TEXT, NOT NULL): Raw name as written in the recipe
# - quantity (REAL, nullable): Quantity from original recipe text
# - unit (TEXT, nullable): Unit from original recipe text
# - fuzz_score (REAL, nullable): Fuzzy match score for matching normalized_name to known foods
# - match_type (TEXT, nullable): Match method (e.g., exact, fuzzy, manual)
# - matched_food_id (INTEGER, nullable): Foreign key to food_info table
# - amount (REAL, nullable): Parsed numeric amount (cleaned version of quantity)
# - normalized_name (TEXT, nullable): Normalized/cleaned food name
# - estimated_grams (REAL, nullable): Estimated gram weight of ingredient
# - match_reviewed (BOOLEAN, nullable): Whether match was manually reviewed
# - review_outcome (TEXT, nullable): Notes or status from review


# Table: recipes
#
# Columns:
# - id (INTEGER, PRIMARY KEY): Unique identifier for the recipe
# - recipe_title (TEXT, NOT NULL): Title of the recipe (e.g. "Chicken Pot Pie")
# - version (TEXT, nullable): Optional version label (e.g. "v1", "original", "low-carb")
# - source_url (TEXT, nullable): Original URL source for the recipe (if applicable)



`recipes` holds one row per recipe and `ingredients` references it via `recipe_id`.

`ingredients` matches the normalzied_name in the `food_info` table and stores the matched ID

## Migrating Data

Use `scripts/migrate_to_sqlite.py` to copy data directly from Google Sheets
into `data/food_info.db`:

```bash
python scripts/migrate_to_sqlite.py
```

The script expects the same Google credentials currently used by the app (via `streamlit.secrets`).


### Running the data pipeline

# python -m food_project.ingestion.parse_recipe_url --url "<your_recipe_url>"
# python -m food_project.processing.ingredient_updater
# python -m food_project.ingestion.match_ingredients_to_food_info
# python -m food_project.ingestion.review_matches 
