import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Connect to Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("food-app-462903-671ca230975a.json", scope)
client = gspread.authorize(creds)
sheet = client.open("food_info_app").sheet1

# Streamlit UI
st.title("Food Info Tracker")

food = st.text_input("Enter a food name:")
calories = st.number_input("Calories", min_value=0)
price = st.number_input("Price ($)", min_value=0.0)
emissions = st.number_input("CO2 Emissions (kg)", min_value=0.0)

if st.button("Save to Sheet"):
    sheet.append_row([food, calories, price, emissions])
    st.success("Saved!")