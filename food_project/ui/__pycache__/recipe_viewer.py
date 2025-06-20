# import streamlit as st
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials
# import pandas as pd

# # --- Step 1: Setup ---
# scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# google_creds_dict = st.secrets["google"]
# creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds_dict, scope)
# client = gspread.authorize(creds)

# # --- Step 2: Unit conversion map ---
# unit_conversion_to_grams = {
#     "g": 1,
#     "kg": 1000,
#     "mg": 0.001,
#     "lb": 453.592,
#     "oz": 28.3495,
#     "tbsp": 15,
#     "tsp": 5,
#     "cup": 240  # general average, not accurate for all ingredients
# }

# def convert_to_grams(amount, unit):
#     try:
#         return float(amount) * unit_conversion_to_grams[unit]
#     except KeyError:
#         st.warning(f"Unit '{unit}' not recognized — skipping conversion.")
#         return None
#     except Exception:
#         st.warning(f"Invalid amount '{amount}' — skipping.")
#         return None

# # --- Step 3: Load Recipes Sheet ---
# try:
#     recipe_sheet = client.open("food_info_app").worksheet("recipes")
#     recipe_rows = recipe_sheet.get_all_records()
#     recipe_df = pd.DataFrame(recipe_rows)
# except Exception as e:
#     st.error(f"Could not load recipe sheet: {e}")
#     st.stop()

# # --- Step 4: Dropdown of recipe titles ---
# recipe_titles = recipe_df["recipe_title"].unique().tolist()
# selected_recipe = st.selectbox("Select a recipe:", ["-- Select --"] + recipe_titles)

# if selected_recipe and selected_recipe != "-- Select --":
#     filtered = recipe_df[recipe_df["recipe_title"] == selected_recipe]
#     st.subheader(f"Ingredients for: {selected_recipe}")

#     totals = {"calories": 0, "water_use_liters": 0, "cost_usd": 0}  # Add fields you care about

#     for _, row in filtered.iterrows():
#         food = row["food_name"]
#         qty = row["quantity"]
#         unit = row["unit"]

#         qty_in_grams = convert_to_grams(qty, unit)
#         if qty_in_grams is None:
#             continue

#         # Lookup food info in your main food sheet
#         try:
#             food_sheet = client.open("food_info_app").sheet1
#             food_names = food_sheet.col_values(2)  # Assuming food names are in column 2

#             if food in food_names:
#                 idx = food_names.index(food) + 1
#                 headers = food_sheet.row_values(1)
#                 values = food_sheet.row_values(idx)

#                 food_data = dict(zip(headers, values))

#                 calories = float(food_data.get("calories_per_100g", 0)) * qty_in_grams / 100
#                 water = float(food_data.get("water_use_liters_per_100g", 0)) * qty_in_grams / 100
#                 cost = float(food_data.get("cost_per_100g_usd", 0)) * qty_in_grams / 100

#                 totals["calories"] += calories
#                 totals["water_use_liters"] += water
#                 totals["cost_usd"] += cost

#                 st.markdown(f"**{food}** - {qty} {unit} ({round(qty_in_grams)}g)")
#                 st.write(f"Calories: {round(calories)} kcal, Water: {round(water)} L, Cost: ${round(cost, 2)}")
#                 st.divider()
#             else:
#                 st.warning(f"{food} not found in food info sheet.")

#         except Exception as e:
#             st.warning(f"Error looking up {food}: {e}")

#     st.subheader("🔢 Total Recipe Impact")
#     st.write(f"**Calories:** {round(totals['calories'])} kcal")
#     st.write(f"**Water Use:** {round(totals['water_use_liters'])} L")
#     st.write(f"**Cost:** ${round(totals['cost_usd'], 2)}")
########### test code ###################
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials

# # Setup Google Sheets auth (copy from your app.py)
# scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# google_creds_dict = {
#     # Paste your Streamlit secrets google dict here OR mock it for local testing
# }
# creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds_dict, scope)
# client = gspread.authorize(creds)

# sheet = client.open("food_info_app").sheet1

# def get_food_info(food_name):
#     """Get nutrition info for one food as dict."""
#     full_food_list = sheet.col_values(2)
#     if food_name in full_food_list:
#         row_index = full_food_list.index(food_name) + 1
#         headers = sheet.row_values(1)[1:]  # skip food name column header
#         row_data = sheet.row_values(row_index)[1:]  # skip food name col
#         return dict(zip(headers, row_data))
#     return None

# def get_recipe_ingredients(recipe_title):
#     """Return list of (food_name, quantity, unit) for a recipe title."""
#     all_recipe_titles = sheet.col_values(1)
#     ingredients = []
#     # Find all rows matching the recipe title in col 1
#     for i, title in enumerate(all_recipe_titles):
#         if title == recipe_title:
#             # Note: gspread rows are 1-indexed, but enumerate starts at 0, so add 1
#             row = i + 1
#             food_name = sheet.cell(row, 5).value    # 5th col is food_name
#             quantity = sheet.cell(row, 6).value     # 6th col is quantity
#             unit = sheet.cell(row, 7).value         # 7th col is unit
#             ingredients.append((food_name, quantity, unit))
#     return ingredients

# def combine_recipe_info(recipe_title):
#     ingredients = get_recipe_ingredients(recipe_title)
#     print(f"Ingredients for '{recipe_title}':")
#     combined_calories = 0.0
    
#     for food_name, quantity, unit in ingredients:
#         info = get_food_info(food_name)
#         if info:
#             # Assuming calories is a key, and quantity/unit conversions are simple numbers
#             cal_per_unit = float(info.get("Calories", "0").replace(" kcal", "").strip())
#             try:
#                 qty = float(quantity)
#             except Exception:
#                 qty = 1  # fallback if quantity is missing or malformed
#             # NOTE: This ignores unit conversion for now (e.g. pounds to grams)
#             total_cal = cal_per_unit * qty
            
#             combined_calories += total_cal
#             print(f" - {food_name}: {quantity} {unit}, {total_cal:.2f} kcal total")
#         else:
#             print(f" - {food_name}: No data found")

#     print(f"\nTotal Calories for recipe '{recipe_title}': {combined_calories:.2f} kcal")

# if __name__ == "__main__":
#     # Replace with your recipe title from your Google Sheet
#     test_recipe = "Simple Mexican Quinoa"
#     combine_recipe_info(test_recipe)
############ new test code ################
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

creds_dict = st.secrets["google"]

print(creds_dict["type"])  # Should print: service_account

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

print("Credentials loaded successfully")
