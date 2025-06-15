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

# Create a text input field for the user to enter a food name
food = st.text_input("Enter a food name:")

# Create a button that the user can click to search for the food
if st.button("Search"):
    # Use column 2 for 'food_name' instead of column 1
    food_list = sheet.col_values(2)

    # Skip the 'Food Query' column in headers
    headers = sheet.row_values(1)[1:]

    # Check if the entered food name is in the list
    if food in food_list:
        # Find the row index of the food name (1-based index)
        row_index = food_list.index(food) + 1

        # Get the full row and skip the 'Food Query' column
        row_data = sheet.row_values(row_index)[1:]

        # Display each field using its header
        for header, value in zip(headers, row_data):
            st.write(f"{header}: {value}")
    else:
        # If the food name is not found, show an error message
        st.error("Food not found in the sheet.")