"""Streamlit interface for manually reviewing fuzzy ingredient matches."""

import streamlit as st
import sqlite3

DB_PATH = "food_info.db"

def get_fuzzy_matches():
    """Return ingredients that were matched by fuzzy logic."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT i.id, i.food_name AS raw_name, i.normalized_name, i.fuzz_score,
               i.match_type,f.normalized_name AS matched_food, f.id AS food_id
        FROM ingredients i
        JOIN food_info f ON i.matched_food_id = f.id
        WHERE i.match_type = 'fuzzy'
        ORDER BY i.fuzz_score DESC
    """).fetchall()
    conn.close()
    return list(rows)

def update_match(ing_id, food_id, match_type, fuzz_score=100):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        UPDATE ingredients
        SET matched_food_id = ?, match_type = ?, fuzz_score = ?
        WHERE id = ?
    """, (food_id, match_type, fuzz_score, ing_id))
    conn.commit()
    conn.close()

def reject_match(ing_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        UPDATE ingredients
        SET matched_food_id = NULL, match_type = NULL, fuzz_score = NULL
        WHERE id = ?
    """, (ing_id,))
    conn.commit()
    conn.close()

def load_food_options():
    """Return a mapping of normalized food names to their IDs."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, normalized_name FROM food_info ORDER BY normalized_name")
    options = cur.fetchall()
    conn.close()
    return {row[1]: row[0] for row in options}

# Streamlit App UI
st.title("🔍 Review Ingredient Matches")

matches = get_fuzzy_matches()
food_options = load_food_options()

if not matches:
    # Nothing to review — show a friendly message
    st.success("✅ No fuzzy matches to review.")
else:
    for row in matches:
        # Show details for each fuzzy match
        with st.expander(f"🔎 {row['raw_name']} → {row['matched_food']} (score: {row['fuzz_score']})"):
            st.markdown(f"- **Normalized:** `{row['normalized_name']}`")
            st.markdown(f"- **Matched to:** `{row['matched_food']}`")
            st.markdown(f"- **Fuzz Score:** `{row['fuzz_score']}`")

            # Three columns: approve, reject, or override
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Approve", key=f"approve_{row['id']}"):
                    update_match(row["id"], row["food_id"], "manual")
                    st.success("Approved.")

            with col2:
                if st.button("❌ Reject", key=f"reject_{row['id']}"):
                    reject_match(row["id"])
                    st.warning("Rejected.")

            with col3:
                override = st.selectbox("🔄 Override Match", ["-- Select --"] + list(food_options.keys()), key=f"override_{row['id']}")
                if override != "-- Select --":
                    new_id = food_options[override]
                    update_match(row["id"], new_id, "manual")
                    st.info(f"Overridden to: {override}")
