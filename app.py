import streamlit as st
import sqlite3
from food_project.ui import recipe_viewer

try:
    app_id = st.secrets["nutritionix"]["app_id"]
    api_key = st.secrets["nutritionix"]["api_key"]
    st.success(f"Loaded Nutritionix credentials from `secrets.toml`")
except Exception as e:
    st.error(f"Failed to load Nutritionix credentials: {e}")

# -------------------------------
# Load distinct food names
# -------------------------------
@st.cache_data
def load_food_list():
    conn = sqlite3.connect("food_info.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT name FROM ingredients ORDER BY name")
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
        SELECT r.title, r.version, r.source_url, i.name, i.amount, i.unit
        FROM recipes r
        JOIN ingredients i ON r.id = i.recipe_id
        WHERE i.name = ?
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

# -------------------------------
# Food dropdown
# -------------------------------
food_list = load_food_list()
selected_food = st.selectbox("Select a food from the list:", ["-- Select --"] + food_list)

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
