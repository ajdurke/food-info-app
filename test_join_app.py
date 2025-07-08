import sqlite3
import streamlit as st
import pandas as pd
from pathlib import Path

# Confirm environment context
st.write("📂 Current Working Directory:", Path.cwd())

# Connect to SQLite database
db_path = Path("food_info.db")
st.write("📦 DB Path Used:", db_path.resolve())
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# Load recipe options
recipes_df = pd.read_sql_query("SELECT id, recipe_title FROM recipes ORDER BY id DESC", conn)
recipe_options = recipes_df["recipe_title"].tolist()

# UI: recipe selector
selected = st.selectbox("Select a recipe:", ["-- Select --"] + recipe_options)

if selected and selected != "-- Select --":
    selected_id = recipes_df[recipes_df["recipe_title"] == selected]["id"].values[0]
    st.code(f"Selected Recipe ID: {selected_id}")

    # Debug: show ingredients directly
    st.markdown("### 🔍 Raw ingredients for selected recipe:")
    raw_ingredients = pd.read_sql_query(
        "SELECT * FROM ingredients WHERE recipe_id = ?", conn, params=(selected_id,))
    st.dataframe(raw_ingredients)

    # JOIN query
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
