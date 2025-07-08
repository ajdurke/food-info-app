import sqlite3
import streamlit as st
import os
import traceback
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

# Track update state
if "update_done" not in st.session_state:
    st.session_state.update_done = False
if "last_recipe_id" not in st.session_state:
    st.session_state.last_recipe_id = None

# 🔗 Recipe Adder UI
st.markdown("### 📥 Add New Recipe from URL")
url_input = st.text_input("Paste a recipe URL:")

if st.button("Add Recipe"):
    if url_input:
        try:
            existing = conn.execute(
                "SELECT id FROM recipes WHERE source_url = ?", (url_input,)
            ).fetchone()

            if existing:
                st.warning(f"⚠️ This recipe already exists (recipe_id = {existing['id']}).")
                st.session_state["selected_recipe_id"] = existing["id"]
            else:
                recipe_data = parse_recipe(url_input)
                recipe_id = save_recipe_and_ingredients(recipe_data)
                st.success(f"✅ Added '{recipe_data['title']}' (recipe_id={recipe_id})")

                # Save ID for auto-selection
                st.session_state["selected_recipe_id"] = recipe_id
                st.session_state["update_done"] = False
                st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to add recipe: {e}")
            st.code(traceback.format_exc())
    else:
        st.warning("Please enter a valid recipe URL.")

# Load recipes from DB
recipes_df = pd.read_sql("SELECT id, recipe_title FROM recipes ORDER BY id", conn)
recipe_options = recipes_df["recipe_title"].tolist()

# Recipe dropdown (manual or auto-select after add)
selected_id = None
if "selected_recipe_id" in st.session_state:
    try:
        selected_id = st.session_state.pop("selected_recipe_id")
        selected_title = recipes_df.loc[recipes_df["id"] == selected_id, "recipe_title"].values[0]
        selected = st.selectbox("Select a recipe:", ["-- Select --"] + recipe_options,
                                index=recipe_options.index(selected_title) + 1)
    except Exception:
        st.warning("Waiting for new recipe to appear...")
        st.stop()
else:
    selected = st.selectbox("Select a recipe:", ["-- Select --"] + recipe_options)
    if selected != "-- Select --":
        selected_id = int(recipes_df.loc[recipes_df["recipe_title"] == selected, "id"].values[0])

# When a valid recipe is selected
if selected_id:
    st.code(f"Selected Recipe ID: {selected_id}")

    if selected_id != st.session_state.get("last_recipe_id"):
        st.session_state.update_done = False
        st.session_state.last_recipe_id = selected_id

    if not st.session_state.update_done:
        with st.spinner("🔄 Parsing and matching ingredients..."):
            update_ingredients(force=True)
            match_ingredients()
        st.session_state.update_done = True
        st.success("✅ Parsing + Matching complete.")
        st.rerun()

    # Show ingredients for this recipe
    st.markdown("### 🔍 Raw ingredients for selected recipe:")
    raw_ingredients = pd.read_sql("SELECT * FROM ingredients WHERE recipe_id = ?", conn, params=(selected_id,))
    st.dataframe(raw_ingredients)

    # Show JOIN result
    st.markdown("### ✅ JOIN Result:")
    query = """
        SELECT
            i.id AS ingredient_id,
            i.recipe_id,
            i.food_name,
            i.amount,
            i.unit,
            i.normalized_name,
            i.matched_food_id,
            f.id AS food_info_id,
            f.normalized_name AS matched_name,
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
        if df.empty:
            st.warning("⚠️ JOIN returned no rows.")
        else:
            def highlight_unmatched(row):
                return ["background-color: #2a2a2a" if pd.isna(row["matched_name"]) else ""] * len(row)
            styled_df = df.style.apply(highlight_unmatched, axis=1)
            st.dataframe(styled_df, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Error running query: {e}")

    # Unmatched ingredients
    unmatched_df = pd.read_sql_query("""
        SELECT * FROM ingredients
        WHERE recipe_id = ? AND matched_food_id IS NULL
    """, conn, params=(selected_id,))
    st.markdown("### ⚠️ Ingredients Missing Matches")
    if unmatched_df.empty:
        st.success("✅ All ingredients are matched.")
    else:
        st.warning(f"⚠️ {len(unmatched_df)} unmatched ingredients found.")

    # Nutrition summary
    st.markdown("### 📊 Nutrition Summary")
    if df.empty:
        st.info("No ingredients found for this recipe.")
    else:
        summary = df[["calories", "protein", "carbs", "fat"]].fillna(0).astype(float).sum()
        st.table(summary.rename("Total"))
