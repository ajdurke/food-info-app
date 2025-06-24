import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

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
    modifiers = ["sliced", "chopped", "fresh", "unsalted", "diced", "minced", "grated", "large", "small"]
    words = name.split()
    name = " ".join([word for word in words if word not in modifiers])
    
    replacements = {
        "all-purpose flour": "flour",
        "yellow onion": "onion",
        "whole milk": "milk",
    }
    return replacements.get(name, name)

def show_recipe_viewer():
    try:
        recipe_sheet = client.open("food_info_app").worksheet("recipes")
        recipe_rows = recipe_sheet.get_all_records()
        recipe_df = pd.DataFrame(recipe_rows)
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

        for _, row in filtered.iterrows():
            food = normalize_ingredient(row["food_name"])
            qty = row["quantity"]
            unit = row["unit"]

            qty_in_grams = convert_to_grams(qty, unit)
            if qty_in_grams is None:
                continue

            try:
                food_sheet = client.open("food_info_app").sheet1
                food_names = [normalize_ingredient(name) for name in food_sheet.col_values(2)]

                if food in food_names:
                    idx = food_names.index(food) + 1
                    headers = food_sheet.row_values(1)
                    values = food_sheet.row_values(idx)

                    food_data = dict(zip(headers, values))

                    row_data = {
                        "ingredient": food,
                        "quantity": f"{qty} {unit}",
                        "grams": round(qty_in_grams, 2),
                    }

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
                    st.warning(f"{food} not found in food info sheet.")

            except Exception as e:
                st.warning(f"Error looking up {food}: {e}")

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
