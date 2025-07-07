import streamlit as st
import sqlite3
import pandas as pd

def show_review_log(db_path="food_info.db"):
    st.header("🧪 Ingredient Review Log")

    # Connect and load data
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            r.id,
            i.food_name AS original_text,
            r.normalized_name,
            r.amount,
            r.unit,
            r.food_score,
            r.unit_score,
            r.used_llm,
            r.used_llm_estimate,
            r.used_nutritionix,
            r.timestamp,
            r.approved
        FROM ingredient_review_log r
        LEFT JOIN ingredients i ON r.ingredient_id = i.id
        ORDER BY r.timestamp DESC
        LIMIT 100
    """)

    rows = cur.fetchall()
    df = pd.DataFrame(rows)

    if df.empty:
        st.info("No review log entries found.")
        return

    # Optional filtering UI
    col1, col2 = st.columns(2)
    with col1:
        show_only_llm = st.checkbox("Only show rows where LLM was used")
    with col2:
        approval_filter = st.selectbox("Filter by approval status", ["All", "pending", "approved", "rejected"])

    if show_only_llm:
        df = df[df["used_llm"] == 1]
    if approval_filter != "All":
        df = df[df["approved"] == approval_filter]

    # Display log
    st.dataframe(df, use_container_width=True)

    conn.close()
