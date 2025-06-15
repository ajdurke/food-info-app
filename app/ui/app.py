import streamlit as st
from ..database.google_sheets_connector import get_food_data

st.title("Food Info Tracker")

food = st.text_input("Enter a food name:")
if st.button("Search"):
    result = get_food_data(food)
    if result:
        st.write(f"Calories: {result['calories']}")
        st.write(f"Price: ${result['price']}")
        st.write(f"CO2 Emissions: {result['emissions']} kg")
    else:
        st.error("Food not found in the sheet.")