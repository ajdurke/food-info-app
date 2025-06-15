import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# Set up Google Sheets API connection (your existing code)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_PATH = os.path.join(BASE_DIR, "food-app-462903-671ca230975a.json")
creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_PATH, scope)
client = gspread.authorize(creds)

try:
    sheet = client.open("food_info_app").sheet1
except Exception as e:
    st.error(f"Could not open Google Sheet: {e}")
    st.stop()

st.title("Food Info Tracker")

food = st.text_input("Enter a food name:")

if st.button("Search"):
    food_list = sheet.col_values(1)
    if food in food_list:
        row_index = food_list.index(food) + 1
        row_data = sheet.row_values(row_index)

        # Since row_data might be shorter if some columns are empty, pad it with empty strings
        expected_columns = 16  # A through P (Food Query + 15 nutrition columns)
        if len(row_data) < expected_columns:
            row_data += [""] * (expected_columns - len(row_data))

        # Map row_data to variables
        # row_data[0] = Food Query (input)
        food_name = row_data[1]
        brand_name = row_data[2]
        serving_qty = row_data[3]
        serving_unit = row_data[4]
        serving_weight_grams = row_data[5]
        nf_calories = row_data[6]
        nf_total_fat = row_data[7]
        nf_saturated_fat = row_data[8]
        nf_cholesterol = row_data[9]
        nf_sodium = row_data[10]
        nf_total_carbohydrate = row_data[11]
        nf_dietary_fiber = row_data[12]
        nf_sugars = row_data[13]
        nf_protein = row_data[14]
        nf_potassium = row_data[15]

        # Display results nicely
        st.write(f"**Food Name:** {food_name}")
        st.write(f"**Brand Name:** {brand_name}")
        st.write(f"**Serving Size:** {serving_qty} {serving_unit} ({serving_weight_grams} g)")
        st.write(f"**Calories:** {nf_calories} kcal")
        st.write(f"**Total Fat:** {nf_total_fat} g")
        st.write(f"**Saturated Fat:** {nf_saturated_fat} g")
        st.write(f"**Cholesterol:** {nf_cholesterol} mg")
        st.write(f"**Sodium:** {nf_sodium} mg")
        st.write(f"**Total Carbohydrate:** {nf_total_carbohydrate} g")
        st.write(f"**Dietary Fiber:** {nf_dietary_fiber} g")
        st.write(f"**Sugars:** {nf_sugars} g")
        st.write(f"**Protein:** {nf_protein} g")
        st.write(f"**Potassium:** {nf_potassium} mg")

    else:
        st.error("Food not found in the sheet.")

# Optional: remove these inputs if you don't want user input for those
# Or you can keep them to add new items etc.
calories = st.number_input("Calories", min_value=0)
price = st.number_input("Price ($)", min_value=0.0)
emissions = st.number_input("CO2 Emissions (kg)", min_value=0.0)
