# This is the main entry point for the Streamlit web app.
# The goal of the app is to display recipe and ingredient
# information stored in a local SQLite database.  The code
# relies on several helper modules within the ``food_project``
# package.  These modules handle things like normalizing
# ingredient text, matching ingredients to nutrition data,
# and presenting recipe information in the browser.

import streamlit as st
import sqlite3
from food_project.ui import recipe_viewer
from food_project.processing.ingredient_updater import update_ingredients
from food_project.ingestion.match_ingredients_to_food_info import match_ingredients


try:
    app_id = st.secrets["nutritionix"]["app_id"]
    api_key = st.secrets["nutritionix"]["api_key"]
    # The ``secrets.toml`` file (not included in version control)
    # holds the Nutritionix API credentials.  Loading them at
    # runtime lets us fetch nutrition data without exposing the
    # keys in the codebase.
    st.success(f"Loaded Nutritionix credentials from `secrets.toml`")
except Exception as e:
    # When running outside Streamlit Cloud or without the secrets
    # file, we can't fetch credentials.  Show an error instead of
    # crashing so the rest of the app can still run for demo
    # purposes.
    st.error(f"Failed to load Nutritionix credentials: {e}")

# -------------------------------
# Load distinct food names
# -------------------------------
# ``st.cache_data`` tells Streamlit to cache the returned
# list so the database isn't queried on every page load.
@st.cache_data
def load_food_list():
    conn = sqlite3.connect("food_info.db")       # open the database file
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT name FROM ingredients ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    # Each row returned is a tuple like ('carrot',)
    # so we pull out just the name from index 0
    return [row[0] for row in rows]

# -------------------------------
# Load food detail rows
# -------------------------------
# Again we cache the results so repeatedly viewing the same
# food won't keep hitting the database.
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
    # ``rows`` is a list of tuples containing recipe title,
    # version, URL, ingredient name, amount and unit.  We just
    # return that raw data so the caller can format it.
    return rows

# -------------------------------
# Branch-based header
# -------------------------------
# Some deployments set a ``STREAMLIT_BRANCH`` secret so we
# can display whether this app is running on staging or
# production.  If the secret isn't set we fall back to
# "unknown".
branch = st.secrets.get("general", {}).get("STREAMLIT_BRANCH", "unknown")

if branch == "staging":
    st.title("Food Info Tracker - Staging Branch")
else:
    st.title("Food Info Tracker")

col1, col2 = st.columns(2)
with col1:
    # Button to re-run the ingredient parsing step. This updates
    # the ``ingredients`` table with structured amounts and units.
    if st.button("🔄 Re-parse Ingredients"):
        with st.spinner("Re-parsing ingredients..."):
            update_ingredients(force=True)
        st.success("✅ Ingredients re-parsed!")

with col2:
    # Button to re-run the matching step that links each ingredient
    # to an entry in the ``food_info`` table. This can be slow so we
    # trigger it manually.
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
    """Show which recipes include the selected food."""
    results = load_food_details(food_name)
    if results:
        st.subheader(f"Recipes that use **{food_name}**:")
        for title, version, url, ingredient, amount, unit in results:
            # Format each recipe nicely with a link back to the source
            st.markdown(f"**{title}** ({version}) — [source]({url})")
            st.write(f"- {ingredient}: {amount} {unit}")
    else:
        st.error("No info found for that food.")

if selected_food != "-- Select --":
    # When the user picks a food, show which recipes use it.
    display_food_info(selected_food)

# -------------------------------
# Recipes section (from external module)
# -------------------------------
# Delegate the heavy lifting of showing recipe data to the
# ``recipe_viewer`` module.  Calling ``show_recipe_viewer``
# inserts its own Streamlit widgets into the page.
recipe_viewer.show_recipe_viewer()
