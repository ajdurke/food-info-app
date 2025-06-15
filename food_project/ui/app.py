import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os 

# Connect to Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]



# Dynamically find the path to the JSON file (this replaces the old line)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_PATH = os.path.join(BASE_DIR, "food-app-462903-671ca230975a.json")
# st.write("Using credentials file at:", JSON_PATH)
creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_PATH, scope)
client = gspread.authorize(creds)
try:
    sheet = client.open("food_info_app").sheet1
except Exception as e:
    st.error(f"Could not open Google Sheet: {e}")
    st.stop()

# Streamlit UI
st.title("Food Info Tracker")

food = st.text_input("Enter a food name:")
if st.button("Search"):
    # Search for the food in the Google Sheet
    food_list = sheet.col_values(1)  # Assuming food names are in the first column
    if food in food_list:
        row_index = food_list.index(food) + 1  # Get the row index (1-based)
        row_data = sheet.row_values(row_index)
        calories = row_data[1]  # Assuming calories are in the second column
        price = row_data[2]     # Assuming price is in the third column
        emissions = row_data[3] # Assuming emissions are in the fourth column

        st.write(f"Calories: {calories}")
        st.write(f"Price: ${price}")
        st.write(f"CO2 Emissions: {emissions} kg")
    else:
        st.error("Food not found in the sheet.")

calories = st.number_input("Calories", min_value=0)
price = st.number_input("Price ($)", min_value=0.0)
emissions = st.number_input("CO2 Emissions (kg)", min_value=0.0)