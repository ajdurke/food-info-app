import sqlite3
import streamlit as st
import os
import pandas as pd
from pathlib import Path
from food_project.ingestion.parse_recipe_url import parse_recipe
from food_project.database.sqlite_connector import save_recipe_and_ingredients
from food_project.processing.ingredient_updater import update_ingredients
from food_project.ingestion.match_ingredients_to_food_info import match_ingredients

# Confirm environment
st.write("📂 Current Working Directory:", Path.cwd())

# Connect to database
db_path = Path(__file__).parent / "food_info.db"
st.write("📦 DB Path Used:", db_path.resolve())
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# 🔗 Recipe Adder UI
st.markdown("### 📥 Add New Recipe from URL")
url_input = st.text_input("Paste a recipe URL:")

if st.button("Add Recipe"):
    if url_input:
        try:
            recipe_data = parse_recipe(url_input)
            recipe_id = save_recipe_and_ingredients(recipe_data)
            st.success(f"✅ Added '{recipe_data['title']}' (recipe_id={recipe_id})")
            update_ingredients(force=True)
            match_ingredients()
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to add recipe: {e}")
    else:
        st.warning("Please enter a valid recipe URL.")

# Load recipes for dropdown
recipes_df = pd.read_sql("SELECT id, recipe_title FROM recipes ORDER BY id", conn)
recipe_options = recipes_df["recipe_title"].tolist()
selected = st.selectbox("Select a recipe:", ["-- Select --"] + recipe_options)

if selected and selected != "-- Select --":
    selected_id = int(recipes_df[recipes_df["recipe_title"] == selected]["id"].values[0])
    st.code(f"Selected Recipe ID: {selected_id}")

    # Preview raw ingredients
    st.markdown("### 🔍 Raw ingredients for selected recipe:")
    raw_ingredients = pd.read_sql("SELECT * FROM ingredients WHERE recipe_id = ?", conn, params=(selected_id,))
    st.dataframe(raw_ingredients)

    # 🔬 Check if recipe 3 has any ingredients
    test_df = pd.read_sql("SELECT * FROM ingredients WHERE recipe_id = 3", conn)
    st.markdown("### 🔎 TEST: Ingredients for Recipe ID 3")
    st.dataframe(test_df)


    # JOIN query using selected recipe_id
    query = """
        SELECT
            i.id AS ingredient_id,
            i.recipe_id,
            i.food_name,
            i.matched_food_id,
            f.id AS food_info_id,
            f.normalized_name,
            f.calories,
            f.protein,
            f.carbs,
            f.fat
        FROM ingredients i
        LEFT JOIN food_info f
        ON CAST(i.matched_food_id AS INTEGER) = CAST(f.id AS INTEGER)
        WHERE i.recipe_id = ?
    """

    try:
        df = pd.read_sql_query(query, conn, params=(selected_id,))
        st.markdown("### ✅ JOIN Result:")
        if df.empty:
            st.warning("⚠️ JOIN returned no rows.")
        else:
            st.dataframe(df)
    except Exception as e:
        st.error(f"❌ Error running query: {e}")

    
    st.markdown("### 📊 Nutrition Summary")
    if df.empty:
        st.info("No ingredients found for this recipe.")
    else:
        # Ensure numeric fields are cleaned up
        summary = df[["calories", "protein", "carbs", "fat"]].fillna(0).astype(float).sum()
        st.table(summary.rename("Total"))

