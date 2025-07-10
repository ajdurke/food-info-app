
import sqlite3
import streamlit as st
import os
import traceback
import pandas as pd
from pathlib import Path
import time  # for optional sleep during debug
from food_project.ingestion.parse_recipe_url import parse_recipe
from food_project.database.sqlite_connector import save_recipe_and_ingredients
from food_project.processing.ingredient_updater import update_ingredients
from food_project.ingestion.match_ingredients_to_food_info import match_ingredients

# Print current working directory for debugging purposes
st.write("📂 Current Working Directory:", Path.cwd())

# Connect to SQLite DB located in the same folder as the script
db_path = Path(__file__).parent / "food_info.db"
st.write("📦 DB Path Used:", db_path.resolve())
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# Initialize session state values to track parsing + matching progress
if "update_done" not in st.session_state:
    st.session_state.update_done = False
if "last_recipe_id" not in st.session_state:
    st.session_state.last_recipe_id = None

# --------------------------------------
# SECTION: Add New Recipe from URL
# --------------------------------------
st.markdown("### 📥 Add New Recipe from URL")
url_input = st.text_input("Paste a recipe URL:")

# When user clicks "Add Recipe"
if st.button("Add Recipe"):
    if url_input:
        try:
            # Check if this recipe already exists by URL
            existing = conn.execute(
                "SELECT id FROM recipes WHERE source_url = ?", (url_input,)
            ).fetchone()

            if existing:
                st.warning(f"⚠️ This recipe already exists (recipe_id = {existing['id']}).")
                st.session_state["selected_recipe_id"] = existing["id"]
            else:
                # Parse and save new recipe and ingredients
                recipe_data = parse_recipe(url_input)
                recipe_id = save_recipe_and_ingredients(recipe_data)
                st.success(f"✅ Added '{recipe_data['title']}' (recipe_id={recipe_id})")

                # Immediately inspect what was saved
                debug_df = pd.read_sql_query(
                    "SELECT * FROM ingredients WHERE recipe_id = ?", conn, params=(recipe_id,)
                )
                st.write("🧪 Just saved ingredients:")
                st.dataframe(debug_df)
                print("🧪 Terminal Debug: Saved ingredients:")
                for row in debug_df.itertuples():
                    print(f" - {row.food_name}")

                # Store recipe ID in session to trigger auto-selection
                st.session_state["selected_recipe_id"] = recipe_id
                st.session_state["update_done"] = False

                # Trigger rerun of the app so dropdown can refresh
                st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to add recipe: {e}")
            st.code(traceback.format_exc())
    else:
        st.warning("Please enter a valid recipe URL.")

# --------------------------------------
# SECTION: Recipe Selector Dropdown
# --------------------------------------
# Load recipe titles + IDs from DB for the dropdown
recipes_df = pd.read_sql("SELECT id, recipe_title FROM recipes ORDER BY id", conn)
recipe_options = recipes_df["recipe_title"].tolist()

selected = "-- Select --"
selected_id = None

# Auto-select the recipe if just added
if "selected_recipe_id" in st.session_state:
    try:
        selected_id = st.session_state.pop("selected_recipe_id")
        selected_title = recipes_df.loc[recipes_df["id"] == selected_id, "recipe_title"].values[0]
        selected = st.selectbox("Select a recipe:", ["-- Select --"] + recipe_options,
                                index=recipe_options.index(selected_title) + 1)
    except Exception:
        # Recipe might not yet appear due to caching/timing issues
        st.warning("Waiting for new recipe to appear...")
        st.stop()
else:
    # Manual selection from dropdown
    selected = st.selectbox("Select a recipe:", ["-- Select --"] + recipe_options)
    if selected != "-- Select --":
        selected_id = int(recipes_df.loc[recipes_df["recipe_title"] == selected, "id"].values[0])

# --------------------------------------
# SECTION: After Recipe is Selected
# --------------------------------------
if selected_id:
    st.code(f"Selected Recipe ID: {selected_id}")

    # Reset update trigger if user picked a different recipe
    if selected_id != st.session_state.get("last_recipe_id"):
        st.session_state.update_done = False
        st.session_state.last_recipe_id = selected_id

    # ✅ PARSE + MATCH (only once per selection)
    if not st.session_state.update_done:
        st.write("⚙️ Starting update_ingredients and match_ingredients...")
        with st.spinner("🔄 Parsing and matching ingredients..."):
            update_ingredients(mode="full")
            match_ingredients()
        st.session_state.update_done = True
        st.success("✅ Parsing + Matching complete.")
        st.rerun()

    # --------------------------------------
    # SECTION: INGREDIENTS + JOIN VIEW
    # --------------------------------------
    st.markdown("### 🔍 Raw ingredients for selected recipe:")
    raw_ingredients = pd.read_sql("SELECT * FROM ingredients WHERE recipe_id = ?", conn, params=(selected_id,))
    st.dataframe(raw_ingredients)

    st.markdown("### ✅ JOIN Result:")
    query = """
        SELECT
            i.id AS ingredient_id,
            i.recipe_id,
            i.food_name,
            i.amount,
            i.unit,
            i.estimated_grams,
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

    # --------------------------------------
    # SECTION: Unmatched ingredients
    # --------------------------------------
    unmatched_df = pd.read_sql_query("""
        SELECT * FROM ingredients
        WHERE recipe_id = ? AND matched_food_id IS NULL
    """, conn, params=(selected_id,))
    st.markdown("### ⚠️ Ingredients Missing Matches")
    if unmatched_df.empty:
        st.success("✅ All ingredients are matched.")
    else:
        st.warning(f"⚠️ {len(unmatched_df)} unmatched ingredients found.")

    # --------------------------------------
    # SECTION: Nutrition summary
    # --------------------------------------
    st.markdown("### 📊 Nutrition Summary")
    if df.empty:
        st.info("No ingredients found for this recipe.")
    else:
        # Only use rows where estimated_grams and calories are not null
        df_valid = df.dropna(subset=["estimated_grams", "calories"])
        # Calculate nutrition per ingredient based on estimated_grams
        for nutrient in ["calories", "protein", "carbs", "fat"]:
            df_valid[nutrient + "_total"] = (
                df_valid[nutrient].astype(float) * df_valid["estimated_grams"].astype(float) / 100
            )
        # Sum up the totals
        summary = df_valid[[nutrient + "_total" for nutrient in ["calories", "protein", "carbs", "fat"]]].sum()
        # Rename for display
        summary.index = ["calories", "protein", "carbs", "fat"]
        st.table(summary.rename("Total (using grams)"))
