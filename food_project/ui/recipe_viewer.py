import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# --- Step 1: Setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
google_creds_dict = st.secrets["google"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds_dict, scope)
client = gspread.authorize(creds)

# --- Step 2: Unit conversion map ---
unit_conversion_to_grams = {
    "g": 1,
    "kg": 1000,
    "mg": 0.001,
    "lb": 453.592,
    "oz": 28.3495,
    "tbsp": 15,
    "tsp": 5,
    "cup": 240  # general average, not accurate for all ingredients
}

def convert_to_grams(amount, unit):
    try:
        return float(amount) * unit_conversion_to_grams[unit]
    except KeyError:
        st.warning(f"Unit '{unit}' not recognized — skipping conversion.")
        return None
    except Exception:
        st.warning(f"Invalid amount '{amount}' — skipping.")
        return None

# --- Step 3: Load Recipes Sheet ---
try:
    recipe_sheet = client.open("food_info_app").worksheet("recipes")
    recipe_rows = recipe_sheet.get_all_records()
    recipe_df = pd.DataFrame(recipe_rows)
except Exception as e:
    st.error(f"Could not load recipe sheet: {e}")
    st.stop()

# --- Step 4: Dropdown of recipe titles ---
recipe_titles = recipe_df["recipe_title"].unique().tolist()
selected_recipe = st.selectbox("Select a recipe:", ["-- Select --"] + recipe_titles)

if selected_recipe and selected_recipe != "-- Select --":
    filtered = recipe_df[recipe_df["recipe_title"] == selected_recipe]
    st.subheader(f"Ingredients for: {selected_recipe}")

    totals = {"calories": 0, "water_use_liters": 0, "cost_usd": 0}  # Add fields you care about

    for _, row in filtered.iterrows():
        food = row["food_name"]
        qty = row["quantity"]
        unit = row["unit"]

        qty_in_grams = convert_to_grams(qty, unit)
        if qty_in_grams is None:
            continue

        # Lookup food info in your main food sheet
        try:
            food_sheet = client.open("food_info_app").sheet1
            food_names = food_sheet.col_values(2)  # Assuming food names are in column 2

            if food in food_names:
                idx = food_names.index(food) + 1
                headers = food_sheet.row_values(1)
                values = food_sheet.row_values(idx)

                food_data = dict(zip(headers, values))

                st.markdown(f"**{food}** - {qty} {unit} ({round(qty_in_grams)}g)")

                for field, val in food_data.items():
                    if field == "food_name":
                        continue

                    display_val = val
                    try:
                        num_val = float(val)
                        if field.endswith("_per_100g"):
                            num_val = num_val * qty_in_grams / 100

                            if field == "calories_per_100g":
                                totals["calories"] += num_val
                            elif field == "water_use_liters_per_100g":
                                totals["water_use_liters"] += num_val
                            elif field == "cost_per_100g_usd":
                                totals["cost_usd"] += num_val

                        display_val = round(num_val, 2)
                    except ValueError:
                        pass

                    st.write(f"{field}: {display_val}")

                st.divider()
            else:
                st.warning(f"{food} not found in food info sheet.")

        except Exception as e:
            st.warning(f"Error looking up {food}: {e}")

    st.subheader("Total Recipe Impact")
    st.write(f"**Calories:** {round(totals['calories'])} kcal")
    st.write(f"**Water Use:** {round(totals['water_use_liters'])} L")
    st.write(f"**Cost:** ${round(totals['cost_usd'], 2)}")

