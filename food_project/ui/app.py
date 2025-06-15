import streamlit as st
from food_app.food_project.ui import app

st.title("Food Info Tracker")

food = st.text_input("Enter a food name:")
if st.button("Search"):
    result = app.get_food_data(food)
    if result:
        st.write(f"Calories: {result['calories']}")
        st.write(f"Price: ${result['price']}")
        st.write(f"CO2 Emissions: {result['emissions']} kg")
    else:
        st.error("Food not found in the sheet.")