import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# Define the scope for Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Load credentials JSON from Streamlit secrets (as dict)
google_creds_dict = st.secrets["google"]

# Convert dict to JSON string and load credentials from the string (not a file)
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds_dict, scope)

# Authorize gspread client
client = gspread.authorize(creds)

try:
    sheet = client.open("food_info_app").sheet1
except Exception as e:
    st.error(f"Could not open Google Sheet: {e}")
    st.stop()

# Set the title of the Streamlit app
st.title("Food Info Tracker (Staging)")

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
