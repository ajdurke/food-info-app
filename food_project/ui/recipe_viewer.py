"""Streamlit components to browse recipes and compute totals."""

import streamlit as st
import sqlite3
import pandas as pd
from rapidfuzz import fuzz, process

unit_conversion_to_grams = {
    "g": 1, "kg": 1000, "mg": 0.001, "lb": 453.592,
    "oz": 28.3495, "tbsp": 15, "tsp": 5, "cup": 240,
}

unit_aliases = {
    "pound": "lb", "pounds": "lb", "lbs": "lb",
    "ounce": "oz", "ounces": "oz",
    "teaspoon": "tsp", "teaspoons": "tsp",
    "tablespoon": "tbsp", "tablespoons": "tbsp",
    "cups": "cup", "count": None, "sheet": None,
}

def normalize_unit(unit):
    unit = unit.lower().strip()
    return unit_aliases.get(unit, unit)

def convert_to_grams(amount, unit):
    unit = normalize_unit(unit)
    if unit is None:
        return None
    try:
        return float(amount) * unit_conversion_to_grams[unit]
    except Exception:
        return None

def normalize_ingredient(name):
    name = name.lower().strip()
    modifiers = ["sliced", "chopped", "fresh", "salted", "unsalted", "diced", "minced", "grated", "large", "small"]
    words = [w for w in name.split() if w not in modifiers]
    simplified = " ".join(words)
    replacements = {
        "all-purpose flour": "flour",
        "yellow onion": "onion",
        "whole milk": "milk",
        "chicken breast or thighs": "chicken",
    }
    return replacements.get(simplified, simplified)

@st.cache_data(ttl=300)
def load_recipe_df():
    conn = sqlite3.connect("food_info.db")
    query = """
        SELECT r.id AS recipe_id,
               r.recipe_title,
               r.version,
               r.source_url,
               i.food_name,
               i.amount AS quantity,
               i.unit
        FROM recipes r
        JOIN ingredients i ON r.id = i.recipe_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=300)
def load_food_data():
    conn = sqlite3.connect("food_info.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM food_info")
    rows = cur.fetchall()
    headers = [d[0] for d in cur.description]
    conn.close()
    return headers, [list(row) for row in rows]

def match_ingredient(name, candidate_names, threshold=85):
    match, score, _ = process.extractOne(name, candidate_names, scorer=fuzz.ratio)
    return match if score >= threshold else None

def show_recipe_viewer():
    if st.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    try:
        recipe_df = load_recipe_df()
    except Exception as e:
        st.error(f"Could not load recipe data: {e}")
        st.stop()

    recipe_titles = recipe_df["recipe_title"].unique().tolist()
    selected_recipe = st.selectbox("Select a recipe:", ["-- Select --"] + recipe_titles)

    if selected_recipe and selected_recipe != "-- Select --":
        filtered = recipe_df[recipe_df["recipe_title"] == selected_recipe]
        st.subheader(f"Ingredients for: {selected_recipe}")

        ingredient_rows = []
        totals = {}

        try:
            headers, food_rows = load_food_data()
            normalized_food_map = {
                normalize_ingredient(row[1]): row for row in food_rows if len(row) > 1
            }
            all_normalized_names = list(normalized_food_map.keys())
        except Exception as e:
            st.error(f"Could not load food data: {e}")
            st.stop()

        for _, row in filtered.iterrows():
            original_name = row["food_name"]
            food = normalize_ingredient(original_name)
            qty = row["quantity"]
            unit = row["unit"]
            qty_in_grams = convert_to_grams(qty, unit)
            if qty_in_grams is None:
                continue

            matched_name = food if food in normalized_food_map else match_ingredient(food, all_normalized_names)

            if matched_name:
                values = normalized_food_map[matched_name]
                food_data = dict(zip(headers, values))
                row_data = {
                    "ingredient": original_name,
                    "quantity": f"{qty} {unit}",
                    "grams": round(qty_in_grams, 2),
                }

                for field, val in food_data.items():
                    if field == "food_name":
                        continue
                    display_val = val
                    numeric_val = None
                    if val is not None:
                        try:
                            numeric_val = float(val)
                            if field.endswith("_per_100g"):
                                numeric_val *= qty_in_grams / 100
                            display_val = round(numeric_val, 2)
                        except (ValueError, TypeError):
                            pass
                    row_data[field] = display_val
                    if numeric_val is not None:
                        totals[field] = totals.get(field, 0) + numeric_val
                ingredient_rows.append(row_data)
            else:
                st.warning(f"{original_name} not found in food info database.")

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
