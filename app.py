# This is the main entry point for the Streamlit web app.
# The goal of the app is to display recipe and ingredient
# information stored in a local SQLite database.  The code
# relies on several helper modules within the ``food_project``
# package.  These modules handle things like normalizing
# ingredient text, matching ingredients to nutrition data,
# and presenting recipe information in the browser.

import os
import streamlit as st
import sqlite3
from food_project.ui import recipe_viewer
from food_project.processing.ingredient_updater import update_ingredients
from food_project.ingestion.match_ingredients_to_food_info import match_ingredients
from food_project.ui.review_log_viewer import show_review_log

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY") or st.secrets["together"]["api_key"]

st.write("🔐 TOGETHER API Key available:", "together" in st.secrets and "api_key" in st.secrets["together"])


try:
    app_id = st.secrets["nutritionix"]["app_id"]
    api_key = st.secrets["nutritionix"]["api_key"]
    st.success(f"Loaded Nutritionix credentials from `secrets.toml`")
except Exception as e:
    st.error(f"Failed to load Nutritionix credentials: {e}")

tab1, tab2, tab3 = st.tabs(["📋 Recipes", "🔍 Ingredient Matcher", "🧪 Review Log"])

with tab1:
    recipe_viewer.show_recipe_viewer()

with tab2:
    st.write("Ingredient matcher not yet implemented here.")

with tab3:
    show_review_log()

# -------------------------------
# Load distinct food names
# -------------------------------
@st.cache_data
def load_food_list():
    conn = sqlite3.connect("food_info.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT food_name FROM ingredients WHERE food_name IS NOT NULL ORDER BY food_name")

    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

# -------------------------------
# Load food detail rows
# -------------------------------
@st.cache_data
def load_food_details(food_name):
    conn = sqlite3.connect("food_info.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.title, r.version, r.source_url, i.food_name, i.amount, i.unit
        FROM recipes r
        JOIN ingredients i ON r.id = i.recipe_id
        WHERE i.food_name = ?
    """, (food_name,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# -------------------------------
# Branch-based header
# -------------------------------
branch = st.secrets.get("general", {}).get("STREAMLIT_BRANCH", "unknown")

if branch == "staging":
    st.title("Food Info Tracker - Staging Branch")
else:
    st.title("Food Info Tracker")

col1, col2 = st.columns(2)
with col1:
    if st.button("🔄 Re-parse Ingredients"):
        with st.spinner("Re-parsing ingredients..."):
            update_ingredients(force=True)
        st.success("✅ Ingredients re-parsed!")

with col2:
    if st.button("🔄 Re-match Ingredients"):
        with st.spinner("Re-matching ingredients..."):
            match_ingredients()
        st.success("✅ Ingredients re-matched!")

# -------------------------------
# Food dropdown
# -------------------------------
food_list = load_food_list()
selected_food = st.selectbox(
    "Select a food from the list:",
    ["-- Select --"] + food_list
)

# -------------------------------
# Show details
# -------------------------------
def display_food_info(food_name):
    results = load_food_details(food_name)
    if results:
        st.subheader(f"Recipes that use **{food_name}**:")
        for title, version, url, ingredient, amount, unit in results:
            st.markdown(f"**{title}** ({version}) — [source]({url})")
            st.write(f"- {ingredient}: {amount} {unit}")
    else:
        st.error("No info found for that food.")

if selected_food != "-- Select --":
    display_food_info(selected_food)

# -------------------------------
# Recipes section (from external module)
# -------------------------------
recipe_viewer.show_recipe_viewer()
