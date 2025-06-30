# import argparse
# import csv
# import sqlite3
# from pathlib import Path


# DEFAULT_DB = Path("food_info.db")


# def init_db(conn: sqlite3.Connection) -> None:
#     cur = conn.cursor()
#     cur.execute(
#         """
#         CREATE TABLE IF NOT EXISTS recipes (
#             id INTEGER PRIMARY KEY,
#             title TEXT NOT NULL,
#             version TEXT,
#             source_url TEXT
#         )
#         """
#     )
#     cur.execute(
#         """
#         CREATE TABLE IF NOT EXISTS ingredients (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             recipe_id INTEGER NOT NULL,
#             name TEXT NOT NULL,
#             amount REAL,
#             unit TEXT,
#             FOREIGN KEY (recipe_id) REFERENCES recipes(id)
#         )
#         """
#     )
#     conn.commit()


# def import_recipes(csv_path: Path, conn: sqlite3.Connection) -> None:
#     cur = conn.cursor()
#     seen_recipes = set()
#     with csv_path.open(newline="", encoding="utf-8") as f:
#         reader = csv.DictReader(f)
#         for row in reader:
#             recipe_id = row.get("recipe_id")
#             if recipe_id is None:
#                 continue
#             recipe_id = int(recipe_id)

#             if recipe_id not in seen_recipes:
#                 cur.execute(
#                     "INSERT OR IGNORE INTO recipes (id, title, version, source_url) VALUES (?, ?, ?, ?)",
#                     (
#                         recipe_id,
#                         row.get("recipe_title") or row.get("title"),
#                         row.get("version"),
#                         row.get("source_url"),
#                     ),
#                 )
#                 seen_recipes.add(recipe_id)

#             cur.execute(
#                 "INSERT INTO ingredients (recipe_id, name, amount, unit) VALUES (?, ?, ?, ?)",
#                 (
#                     recipe_id,
#                     row.get("food_name") or row.get("name"),
#                     row.get("quantity"),
#                     row.get("unit"),
#                 ),
#             )
#     conn.commit()


# def main() -> None:
#     parser = argparse.ArgumentParser(description="Import recipes CSV into SQLite database")
#     parser.add_argument("csv_file", help="Path to recipes CSV file")
#     parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite DB file to populate")
#     args = parser.parse_args()

#     db_path = Path(args.db)
#     conn = sqlite3.connect(db_path)
#     init_db(conn)
#     import_recipes(Path(args.csv_file), conn)
#     conn.close()


# if __name__ == "__main__":
#     main()
