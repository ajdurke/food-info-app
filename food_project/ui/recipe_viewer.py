import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from rapidfuzz import fuzz, process

# --- Google Sheets client setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# --- Unit conversion map and aliases ---
unit_conversion_to_grams = {
    "g": 1,
    "kg": 1000,
    "mg": 0.001,
    "lb": 453.592,
    "oz": 28.3495,
    "tbsp": 15,
    "tsp": 5,
    "cup": 240,
}

unit_aliases = {
    "pound": "lb",
    "pounds": "lb",
    "lbs": "lb",
    "ounce": "oz",
    "ounces": "oz",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "cups": "cup",
    "count": None,
    "sheet": None,
}

def normalize_unit(unit):
    unit = unit.lower().strip()
    return unit_aliases.get(unit, unit)

def convert_to_grams(amount, unit):
    unit = normalize_unit(unit)
    if unit is None:
        st.warning(f"Unit '{unit}' not recognized — skipping conversion.")
        return None
    try:
        return float(amount) * unit_conversion_to_grams[unit]
    except KeyError:
        st.warning(f"Unit '{unit}' not recognized — skipping conversion.")
        return None
    except Exception:
        st.warning(f"Invalid amount '{amount}' — skipping.")
        return None

def normalize_ingredient(name):
    name = name.lower().strip()
    modifiers = ["sliced", "chopped", "fresh", "salted","unsalted", "diced", "minced", "grated", "large", "small"]
    words = name.split()
    words = [word for word in words if word not in modifiers]
    name = " ".join(words)

    replacements = {
        "all-purpose flour": "flour",
        "yellow onion": "onion",
        "whole milk": "milk",
        "chicken breast or thighs": "chicken",

    }
    return replacements.get(name, name)

@st.cache_data(ttl=300)
def load_recipe_df():
    recipe_sheet = client.open("food_info_app").worksheet("recipes")
    recipe_rows = recipe_sheet.get_all_records()
    return pd.DataFrame(recipe_rows)

@st.cache_data(ttl=300)
def load_food_sheet():
    food_sheet = client.open("food_info_app").sheet1
    headers = food_sheet.row_values(1)
    values = food_sheet.get_all_values()[1:]  # Skip header
    return headers, values

def match_ingredient(name, candidate_names, threshold=85):
    match, score, _ = process.extractOne(name, candidate_names, scorer=fuzz.ratio)
    if score >= threshold:
        return match
    return None

def show_recipe_viewer():
    if st.button("Refresh Data"):
        st.cache_data.clear()
        st.experimental_rerun()

    try:
        recipe_df = load_recipe_df()
    except Exception as e:
        st.error(f"Could not load recipe sheet: {e}")
        st.stop()

    recipe_titles = recipe_df["recipe_title"].unique().tolist()
    selected_recipe = st.selectbox(
        "Select a recipe:", ["-- Select --"] + recipe_titles, key="recipe_select"
    )

    if selected_recipe and selected_recipe != "-- Select --":
        filtered = recipe_df[recipe_df["recipe_title"] == selected_recipe]
        st.subheader(f"Ingredients for: {selected_recipe}")

        ingredient_rows = []
        totals = {}

        try:
            headers, food_rows = load_food_sheet()
            normalized_food_map = {
                normalize_ingredient(row[1]): row for row in food_rows if len(row) > 1
            }
            all_normalized_names = list(normalized_food_map.keys())
        except Exception as e:
            st.error(f"Could not load food sheet: {e}")
            st.stop()

        for _, row in filtered.iterrows():
            original_name = row["food_name"]
            food = normalize_ingredient(original_name)
            qty = row["quantity"]
            unit = row["unit"]

            qty_in_grams = convert_to_grams(qty, unit)
            if qty_in_grams is None:
                continue

            # Try exact match, then fuzzy match fallback
            matched_name = food if food in normalized_food_map else match_ingredient(food, all_normalized_names)

            if matched_name:
                values = normalized_food_map[matched_name]

                row_data = {
                    "ingredient": original_name,
                    "quantity": f"{qty} {unit}",
                    "grams": round(qty_in_grams, 2),
                }

                food_data = dict(zip(headers, values))

                for field, val in food_data.items():
                    if field == "food_name":
                        continue

                    display_val = val
                    numeric_val = None
                    try:
                        numeric_val = float(val)
                        if field.endswith("_per_100g"):
                            numeric_val = numeric_val * qty_in_grams / 100
                        display_val = round(numeric_val, 2)
                    except ValueError:
                        pass

                    row_data[field] = display_val
                    if numeric_val is not None:
                        totals[field] = totals.get(field, 0) + numeric_val

                ingredient_rows.append(row_data)
            else:
                st.warning(f"{original_name} not found in food info sheet.")

        if ingredient_rows:
            df = pd.DataFrame(ingredient_rows)
            totals_row = {col: "" for col in df.columns}
            totals_row["ingredient"] = "Total"
            for key, value in totals.items():
                if key in df.columns:
                    totals_row[key] = round(value, 2)
            df = pd.concat([df, pd.DataFrame([totals_row])], ignore_index=True)
            st.dataframe(df)
        else:
            st.info("No ingredients found for this recipe.")
