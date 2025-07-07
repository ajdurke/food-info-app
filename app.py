import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import sqlite3
import streamlit as st
st.write("📦 app.py loaded")
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

with tab1:
    conn = get_connection()
    st.write("📍 DB path in app:", conn.execute("PRAGMA database_list").fetchone()[2])
    st.markdown(f"📍 DB path in app: `{os.path.abspath('food_info.db')}`")

    st.subheader("🧬 Schema Debug")

    def format_table_schema(cursor, table_name):
        return pd.DataFrame(
            cursor.execute(f"PRAGMA table_info({table_name})").fetchall(),
            columns=["cid", "name", "type", "notnull", "dflt_value", "pk"]
        )

    st.markdown("#### 🧾 Ingredients table schema")
    st.dataframe(format_table_schema(conn, "ingredients"))

    st.markdown("#### 🧾 Food_info table schema")
    st.dataframe(format_table_schema(conn, "food_info"))


    st.write("📊 ALL recipe_ids in ingredients table:")
    recipe_ids_in_ingredients = pd.read_sql("SELECT DISTINCT recipe_id FROM ingredients", conn)
    st.dataframe(recipe_ids_in_ingredients)


    @st.cache_data(ttl=600)
    def load_recipes():
        return pd.read_sql_query("SELECT id, recipe_title FROM recipes ORDER BY id DESC", conn)

    recipes_df = load_recipes()
    recipe_options = recipes_df["recipe_title"].tolist()
    selected = st.selectbox("Select an existing recipe:", ["-- Select --"] + recipe_options)

    # Add new recipe
    st.markdown("### 📥 Add New Recipe")
    url_input = st.text_input("Paste recipe URL:")
    if st.button("Add Recipe from URL"):
        if url_input:
            try:
                recipe_data = parse_recipe(url_input)
                recipe_id = save_recipe_and_ingredients(recipe_data)
                st.success(f"✅ Added '{recipe_data['title']}' to the database.")
                st.write("🚀 Calling update_ingredients")
                update_ingredients(force=True)
                match_ingredients()
                st.rerun()
            except Exception as e:
                st.error(f"Failed to parse or insert recipe: {e}")
        else:
            st.warning("Please enter a valid recipe URL.")

    if selected and selected != "-- Select --":
        selected_id = recipes_df[recipes_df["recipe_title"] == selected]["id"].values[0]
        st.code(f"DEBUG SQL PARAMS — selected_id: {selected_id}")

        # 🔬 Raw SQL join output to validate matched_food_id join
        st.markdown("### 🧪 Manual SQL Join Debug Output")
        debug_join = conn.execute("""
            SELECT i.id AS ingredient_id,
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
            LEFT JOIN food_info f ON i.matched_food_id = f.id
            WHERE i.recipe_id = ?
        """, (selected_id,)).fetchall()

        if debug_join:
            st.dataframe([dict(row) for row in debug_join])
        else:
            st.warning("⚠️ SQL join returned no rows.")


        # Check if this recipe has unprocessed ingredients
        raw_ingredient_count = pd.read_sql_query("""
            SELECT COUNT(*) as count FROM ingredients
            WHERE recipe_id = ? AND (normalized_name IS NULL OR amount IS NULL)
        """, conn, params=(selected_id,)).iloc[0]["count"]

        # NEW: Display full ingredients table regardless of recipe_id
        st.markdown("### 🐞 DEBUG: Full ingredients table")
        df_all_ingredients = pd.read_sql_query("SELECT * FROM ingredients", conn)
        st.dataframe(df_all_ingredients)

        # Then filter by recipe_id only
        st.markdown("### 🐞 DEBUG: Ingredients with selected recipe_id")
        df_by_recipe = df_all_ingredients[df_all_ingredients["recipe_id"] == selected_id]
        st.dataframe(df_by_recipe)

        # Add this to your debug section:
        st.write("🔬 Matched food_info nutrition values:")
        matched_ids = tuple(df_by_recipe["matched_food_id"].dropna().astype(int))
        if matched_ids:
            st.dataframe(pd.read_sql(f"""
                SELECT id, normalized_name, calories, protein, fat, carbs
                FROM food_info
                WHERE id IN {matched_ids}
            """, conn))
        else:
            st.write("No matched_food_id values found.")

        if raw_ingredient_count > 0:
            st.warning("🔄 Some ingredients are unparsed — running updater...")
            update_ingredients(force=True)
            match_ingredients()

        # Pull parsed ingredients
        # query = """
        #     SELECT i.food_name,
        #         i.amount,
        #         i.quantity,
        #         i.unit,
        #         i.normalized_name,
        #         i.matched_food_id,
        #         f.calories,
        #         f.protein,
        #         f.carbs,
        #         f.fat
        #     FROM ingredients i
        #     LEFT JOIN food_info f ON i.matched_food_id = f.id
        #     WHERE i.recipe_id = ?
        # """
        # ingredients = pd.read_sql_query(query, conn, params=(selected_id,))
        ingredients = pd.read_sql_query("""
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
            LEFT JOIN food_info f ON i.matched_food_id = f.id
            WHERE i.recipe_id = 3;
        """, conn)

        # Show raw values before formatting
        st.markdown("### 🧪 Raw parsed ingredient join result")
        st.dataframe(ingredients)


        st.write("📌 Selected Recipe ID:", selected_id)

        st.write("📌 Total ingredients with this recipe_id:")
        total_ingredients = pd.read_sql("SELECT COUNT(*) AS count FROM ingredients WHERE recipe_id = ?", conn, params=(selected_id,))
        st.write(total_ingredients)

        st.write("📄 Raw ingredients for this recipe_id:")
        raw = pd.read_sql("SELECT * FROM ingredients WHERE recipe_id = ?", conn, params=(selected_id,))
        st.dataframe(raw)

        st.write("⚠️ Ingredients missing match (matched_food_id is NULL):")
        unmatched = pd.read_sql("""
        SELECT * FROM ingredients
        WHERE recipe_id = ? AND matched_food_id IS NULL
        """, conn, params=(selected_id,))
        st.dataframe(unmatched)

        st.write("🧠 Sample food_info entries:")
        food_info_check = pd.read_sql("SELECT id, normalized_name FROM food_info ORDER BY id DESC LIMIT 10", conn)
        st.dataframe(food_info_check)

        st.write("🔎 Data types of matched_food_id and food_info.id")
        st.code(str(df_by_recipe.dtypes))
        st.code(str(food_info_check.dtypes))

        st.markdown(f"### 🍴 Ingredients for '{selected}'")
        st.dataframe(ingredients)

        st.markdown("### 📊 Nutrition Summary")
        if ingredients.empty:
            st.info("No ingredients found.")
        else:
            missing = ingredients[ingredients["calories"] == "—"]
            if not missing.empty:
                st.warning(f"⚠️ Missing nutrition data for: {', '.join(missing['food_name'])}")
            totals = ingredients[["calories", "protein", "carbs", "fat"]].replace("—", 0).astype(float).sum()
            st.table(totals.rename("Total"))

        # Debug preview
        st.write("🧾 Sample of parsed ingredients:")
        st.dataframe(pd.read_sql_query(
            "SELECT id, food_name, quantity, amount, unit, normalized_name FROM ingredients WHERE recipe_id = ?",
            conn, params=(selected_id,)
        ))

with tab2:
    st.markdown("## 🧪 Review Fuzzy Matches")
    matches = get_fuzzy_matches()
    if not matches:
        st.success("✅ No fuzzy matches to review.")
    else:
        for row in matches[:20]:
            with st.expander(f"{row['raw_name']} → {row['matched_food']}"):
                st.markdown(f"- **Normalized:** `{row['normalized_name']}`")
                st.markdown(f"- **Fuzz Score:** `{row['fuzz_score']}`")
                st.markdown(f"- **Match Type:** `{row['match_type']}`")
        st.info("More detailed review available via CLI or future admin tab.")

    st.markdown("---")
    st.markdown("## 🧾 Ingredient Parsing Logs")
    show_review_log()

