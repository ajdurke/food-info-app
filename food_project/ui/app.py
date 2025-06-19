import streamlit as st  # Import Streamlit for creating web apps
import gspread  # Import gspread for interacting with Google Sheets
from oauth2client.service_account import ServiceAccountCredentials  # Import credentials for Google Sheets
import os  # Import os for file path operations

# Set the scope of permissions needed for Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Dynamically find the path to the JSON file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_PATH = os.path.join(BASE_DIR, "food-app-462903-671ca230975a.json")

# Load the credentials from the JSON file
creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_PATH, scope)

# Authorize the client with the credentials
client = gspread.authorize(creds)

# Try to open the Google Sheet named "food_info_app"
try:
    sheet = client.open("food_info_app").sheet1
except Exception as e:
    # If there's an error, show an error message and stop the app
    st.error(f"Could not open Google Sheet: {e}")
    st.stop()

# Set the title of the Streamlit app
st.title("Food Info Tracker")

# Get all food names for dropdown
food_list = sheet.col_values(2)  # 'food_name' column
food_list = list(set(food_list))  # Remove duplicates if any
food_list.sort()  # Alphabetical order

# Dropdown selector
selected_food = st.selectbox("Select a food from the list:", ["-- Select --"] + food_list)

# Function to display food info given a food name
def display_food_info(food_name):
    full_food_list = sheet.col_values(2)
    if food_name in full_food_list:
        row_index = full_food_list.index(food_name) + 1
        headers = sheet.row_values(1)[1:]  # Skip 'Food Query'
        row_data = sheet.row_values(row_index)[1:]  # Skip 'Food Query' column

        for header, value in zip(headers, row_data):
            st.write(f"{header}: {value}")
    else:
        st.error("Food not found in the sheet.")

# Show details for dropdown selection
if selected_food != "-- Select --":
    display_food_info(selected_food)
