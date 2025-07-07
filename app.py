# app.py

import os
import sqlite3
import streamlit as st
import pandas as pd

from food_project.database.sqlite_connector import get_connection
from food_project.database.nutritionix_service import get_nutrition_data
from food_project.database.sqlite_connector import save_recipe_and_ingredients
from food_project.ingestion.parse_recipe_url import parse_recipe
from food_project.ui.review_log_viewer import show_review_log
from food_project.ui.review_matches_app import get_fuzzy_matches

from food_project.processing.ingredient_updater import update_ingredients
from food_project.ingestion.match_ingredients_to_food_info import match_ingredients

# Title banner for environment
branch = st.secrets.get("general", {}).get("STREAMLIT_BRANCH", "main")
st.title("📊 Food Info Tracker" + (" — Staging" if branch == "staging" else ""))

# Set up tabs
tab1, tab2 = st.tabs(["🍽 Recipes & Nutrition", "🧪 Review Matches"])

# --------------------------------------------
# Tab 1: Recipe Viewer + Add New Recipe
# --------------------------------------------
with tab1:
    conn = get_connection()

    # Fetch existing recipes
    @st.cache_data(ttl=600)
    def load_recipes():
        df = pd.read_sql_query("SELECT id, recipe_title FROM recipes ORDER BY id DESC", conn)
        return df

    recipes_df = load_recipes()
    recipe_options = recipes_df["recipe_title"].tolist()
    selected = st.selectbox("Select an existing recipe:", ["-- Select --"] + recipe_options)

    # Option to add a new recipe from URL
    st.markdown("### 📥 Add New Recipe")
    url_input = st.text_input("Paste recipe URL:")
    if st.button("Add Recipe from URL"):
        if url_input:
            try:
                recipe_data = parse_recipe(url_input)
                recipe_id = save_recipe_and_ingredients(recipe_data)
                st.success(f"✅ Added '{recipe_data['title']}' to the database.")
                update_ingredients(force=True)
                match_ingredients()
                st.rerun()
            except Exception as e:
                st.error(f"Failed to parse or insert recipe: {e}")
        else:
            st.warning("Please enter a valid recipe URL.")

    # Nutrition display for selected recipe
    if selected and selected != "-- Select --":
        selected_id = recipes_df[recipes_df["recipe_title"] == selected]["id"].values[0]
        query = f"""
            SELECT i.food_name, i.amount, i.unit, i.normalized_name, f.calories, f.protein, f.carbs, f.fat
            FROM ingredients i
            LEFT JOIN food_info f ON i.matched_food_id = f.id
            WHERE i.recipe_id = ?
        """
        ingredients = pd.read_sql_query(query, conn, params=(selected_id,))

        st.markdown(f"### 🍴 Ingredients for '{selected}'")
        st.dataframe(ingredients)

        st.markdown("### 📊 Nutrition Summary")
        if ingredients.empty:
            st.info("No ingredients found.")
        else:
            missing = ingredients[ingredients["calories"].isnull()]
            if not missing.empty:
                st.warning(f"⚠️ Missing nutrition data for: {', '.join(missing['food_name'])}")

            totals = ingredients[["calories", "protein", "carbs", "fat"]].sum(numeric_only=True)
            st.table(totals.rename("Total"))

# --------------------------------------------
# Tab 2: Review Matches, Normalization, LLM
# --------------------------------------------
with tab2:
    st.markdown("## 🧪 Review Fuzzy Matches")
    matches = get_fuzzy_matches()
    if not matches:
        st.success("✅ No fuzzy matches to review.")
    else:
        for row in matches[:20]:  # Display first 20
            with st.expander(f"{row['raw_name']} → {row['matched_food']}"):
                st.markdown(f"- **Normalized:** `{row['normalized_name']}`")
                st.markdown(f"- **Fuzz Score:** `{row['fuzz_score']}`")
                st.markdown(f"- **Match Type:** `{row['match_type']}`")
        st.info("More detailed review available via CLI or future admin tab.")

    st.markdown("---")
    st.markdown("## 🧾 Ingredient Parsing Logs")
    show_review_log()
