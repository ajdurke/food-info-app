# """Utility to migrate data from Google Sheets to a local SQLite database."""

# import gspread
# import streamlit as st
# from oauth2client.service_account import ServiceAccountCredentials

# from food_project.database.sqlite_connector import get_connection, init_db


# SHEET_NAME = "food_info_app"
# RECIPES_WORKSHEET = "recipes"


# def get_gsheet_client():
#     scope = [
#         "https://spreadsheets.google.com/feeds",
#         "https://www.googleapis.com/auth/drive",
#     ]
#     creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google"], scope)
#     return gspread.authorize(creds)


# def migrate(db_path="data/food_info.db"):
#     client = get_gsheet_client()
#     recipe_ws = client.open(SHEET_NAME).worksheet(RECIPES_WORKSHEET)

#     conn = get_connection(db_path)
#     init_db(conn)
#     cur = conn.cursor()

#     recipe_rows = recipe_ws.get_all_records()
#     seen_recipes = set()

#     for row in recipe_rows:
#         recipe_id = row.get("recipe_id")
#         recipe_title = row.get("recipe_title")
#         version = row.get("version")
#         source_url = row.get("source_url")
#         food_name = row.get("food_name")
#         quantity = row.get("quantity")
#         unit = row.get("unit")

#         if recipe_id not in seen_recipes:
#             cur.execute(
#                 """INSERT OR IGNORE INTO recipes (id, recipe_title, version, source_url)
#                        VALUES (?, ?, ?, ?)""",
#                 (recipe_id, recipe_title, version, source_url),
#             )
#             seen_recipes.add(recipe_id)

#         cur.execute(
#             """INSERT INTO ingredients (recipe_id, food_name, quantity, unit)
#                    VALUES (?, ?, ?, ?)""",
#             (recipe_id, food_name, quantity, unit),
#         )

#     conn.commit()
#     conn.close()


# if __name__ == "__main__":
#     migrate()

