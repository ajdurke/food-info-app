import sqlite3
import streamlit as st
import pandas as pd
from pathlib import Path

# Confirm where we are and what DB we’re loading
st.write("📂 Current Working Directory:", Path.cwd())

# 🔌 Connect to the SQLite database
db_path = Path(__file__).parent / "food_info.db"
st.write("📦 DB Path Used:", db_path.resolve())
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# 🔍 Run a simple LEFT JOIN query
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
    WHERE i.recipe_id = 3
"""

try:
    df = pd.read_sql_query(query, conn)
    st.markdown("### ✅ JOIN Result:")
    if df.empty:
        st.warning("⚠️ JOIN returned no rows.")
    else:
        st.dataframe(df)
except Exception as e:
    st.error(f"❌ Error running query: {e}")
