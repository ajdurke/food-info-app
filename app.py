import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from food_project.ui import recipe_viewer
import os
import json

#################################################

# Tell Google what kind of access we want (view and edit spreadsheets)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Get the private Google service account info stored in Streamlit's secrets
# This is like logging in to Google with a special app account
google_creds_dict = st.secrets["google"]

# Use that login info to create credentials the gspread library can use
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds_dict, scope)

# Connect to Google Sheets using the authorized credentials
client = gspread.authorize(creds)

import pprint
pprint.pprint(st.secrets["google"])

# Try to open the Google Sheet named "food_info_app"
# If it fails, show an error in the app and stop running
try:
    sheet = client.open("food_info_app").sheet1
except Exception as e:
    st.error(f"Could not open Google Sheet: {e}")
    st.stop()

############################################

# Determine which branch is running based on the environment variable
branch = st.secrets["general"].get("STREAMLIT_BRANCH", "unknown")

# Show a different title depending on the branch
if branch == "staging":
    st.title("Food Info Tracker - Staging Branch")
else:
    st.title("Food Info Tracker")

# Get all the values in the 2nd column (food names)
food_list = sheet.col_values(2)

# Remove duplicates and sort alphabetically
food_list = list(set(food_list))
food_list.sort()

# Create a dropdown menu with the food names
selected_food = st.selectbox("Select a food from the list:", ["-- Select --"] + food_list)

# Function that finds and shows the info for a selected food
# It matches the name with the sheet, then displays all the data in that row
def display_food_info(food_name):
    full_food_list = sheet.col_values(2)
    if food_name in full_food_list:
        row_index = full_food_list.index(food_name) + 1  # +1 because sheets are 1-indexed
        headers = sheet.row_values(1)[1:]  # Skip the first column header ('Food Query')
        row_data = sheet.row_values(row_index)[1:]  # Skip the first column data

        # Show each piece of data with its corresponding label
        for header, value in zip(headers, row_data):
            st.write(f"{header}: {value}")
    else:
        st.error("Food not found in the sheet.")

# If the user selected a food, display its info
if selected_food != "-- Select --":
    display_food_info(selected_food)

