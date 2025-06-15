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
    # Get all the food names from the first column of the Google Sheet
    food_list = sheet.col_values(1)

    # Check if the entered food name is in the list
    if food in food_list:
        # Find the row index of the food name (1-based index)
        row_index = food_list.index(food) + 1

        # Get all the data from the row where the food name is found
        row_data = sheet.row_values(row_index)

        # Extract calories, price, and emissions from the row data
        calories = row_data[1]
        price = row_data[2]
        emissions = row_data[3]

        # Display the calories, price, and emissions in the app
        st.write(f"Calories: {calories}")
        st.write(f"Price: ${price}")
        st.write(f"CO2 Emissions: {emissions} kg")
    else:
        # If the food name is not found, show an error message
        st.error("Food not found in the sheet.")