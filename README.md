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


## 📚 Function Reference

### 📁 `./`
#### └── 📄 `app.py`
- **`display_food_info`** – Displays a table of recipes and how they use a given ingredient.
- **`load_food_details`** – Retrieves recipes and ingredient info for a selected food name.
- **`load_food_list`** – Fetches all unique normalized ingredient names from the ingredients table, used for dropdowns.

### 📁 `food_project/archive/`
#### └── 📄 `google_sheets_connector.py`
- **`get_food_data`** – Reads a row of food data from Google Sheets given a name.
- **`get_sheet`** – Opens the first worksheet of a Google Sheet using Streamlit credentials.

#### └── 📄 `import_csv_to_sqlite.py`
- **`import_recipes`** – Inserts recipe and ingredient data from CSV into the local SQLite database.
- **`init_db`** – Creates the recipes and ingredients tables if they do not exist.
- **`main`** – Handles command-line execution for running a script.

#### └── 📄 `import_food_info.py`
- **`import_food_data`** – Loads nutrition data from CSV and inserts into food_info table.
- **`init_food_table`** – Drops and recreates the food_info table with standard schema.
- **`parse_float`** – Safely converts a string to a float; returns None if not valid.

#### └── 📄 `migrate_to_sqlite.py`
- **`get_gsheet_client`** – Internal helper used to support data parsing, matching, or UI rendering.
- **`migrate`** – Internal helper used to support data parsing, matching, or UI rendering.

### 📁 `food_project/database/`
#### └── 📄 `nutritionix_service.py`
- **`_fetch_from_api`** – Sends a query to the Nutritionix API and returns raw JSON results.
- **`get_nutrition_data`** – Fetches nutrition data for a food, using cache if available, API otherwise.

#### └── 📄 `sqlite_connector.py`
- **`get_connection`** – Creates and returns a SQLite database connection with dictionary row access.
- **`init_db`** – Creates the recipes and ingredients tables if they do not exist.
- **`save_recipe_and_ingredients`** – Saves a recipe and its list of ingredients into the database.

### 📁 `food_project/dev/`
#### └── 📄 `create_fake_food_info.py`
- **`seed_fake_food_info`** – Internal helper used to support data parsing, matching, or UI rendering.

#### └── 📄 `fetch_nutritionix.py`
- **`main`** – Handles command-line execution for running a script.

### 📁 `food_project/ingestion/`
#### └── 📄 `match_ingredients_to_food_info.py`
- **`main`** – Handles command-line execution for running a script.
- **`match_ingredients`** – Assigns the best matching food_info entry for each parsed ingredient.

#### └── 📄 `parse_recipe_url.py`
- **`main`** – Handles command-line execution for running a script.
- **`parse_recipe`** – Extracts ingredients and title from a recipe webpage.

#### └── 📄 `populate_food_info.py`
- **`clear_existing_data`** – Deletes all rows from the food_info table.
- **`fetch_and_insert`** – Fetches nutrition info for a food and inserts into the database.
- **`main`** – Handles command-line execution for running a script.
- **`read_food_list`** – Reads a list of food names from a text file.

#### └── 📄 `review_food_info.py`
- **`main`** – Handles command-line execution for running a script.
- **`review_food_info`** – CLI for inspecting entries in food_info and manually approving them.

#### └── 📄 `review_matches.py`
- **`main`** – Handles command-line execution for running a script.
- **`review_matches`** – CLI for reviewing fuzzy matches and selecting corrections.

### 📁 `food_project/processing/`
#### └── 📄 `ingredient_updater.py`
- **`main`** – Handles command-line execution for running a script.
- **`update_ingredients`** – Parses raw ingredients into structured fields like amount and unit.

#### └── 📄 `matcher.py`
- **`fetch_db_food_matches`** – Gets fuzzy matches for a normalized name against entries in food_info.
- **`fetch_food_matches`** – Returns top fuzzy string matches for a given food name.

#### └── 📄 `normalization.py`
- **`is_countable_item`** – Internal helper used to support data parsing, matching, or UI rendering.
- **`normalize_food_name`** – Cleans and standardizes food names for matching.
- **`parse_ingredient`** – Breaks down an ingredient string into quantity, unit, and name.

#### └── 📄 `units.py`
- **`extract_unit_size`** – Parses text like '(16 oz)' to extract quantity and unit.

### 📁 `food_project/ui/`
#### └── 📄 `recipe_viewer.py`
- **`convert_to_grams`** – Converts ingredient quantity and unit into an estimated gram value.
- **`load_food_data`** – Loads full contents of the food_info table into a DataFrame.
- **`load_recipe_df`** – Loads all recipe and ingredient data into a DataFrame.
- **`match_ingredient`** – Performs fuzzy matching of a food name against known food_info items.
- **`normalize_ingredient`** – Simplifies food name (e.g., 'organic 2% milk' → 'milk').
- **`normalize_unit`** – Maps unit aliases (like tbsp, tablespoon) to standardized unit names.
- **`show_recipe_viewer`** – Displays parsed recipes and totals in the Streamlit UI.

#### └── 📄 `review_matches_app.py`
- **`get_fuzzy_matches`** – Gets fuzzy-matched ingredients needing review for approval UI.
- **`load_food_options`** – Loads all available food_info options into a lookup dict.
- **`reject_match`** – Removes an incorrect food match from an ingredient.
- **`update_match`** – Sets a new food_info match for an ingredient.
