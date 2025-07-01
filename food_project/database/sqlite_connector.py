"""Utility helpers for working with the local SQLite database."""

import sqlite3
from pathlib import Path

# Default path to the SQLite database file.  The path can be
# overridden when calling ``get_connection``.
DB_PATH = Path("food_info.db")

def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Return a connection to the SQLite database."""
    # Ensure the parent directory exists before connecting
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    # ``row_factory`` makes rows behave like dictionaries so we can
    # access columns by name.
    conn.row_factory = sqlite3.Row
    return conn

def init_db(conn: sqlite3.Connection) -> None:
    """Drop and recreate ``food_info`` table; ensure other tables exist."""
    print("⚙️ init_db() is recreating the food_info table")
    cur = conn.cursor()

    # Recreate ``food_info`` table from scratch
    cur.execute("DROP TABLE IF EXISTS food_info")
    cur.execute(
        """
        CREATE TABLE food_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_name TEXT NOT NULL,
            normalized_name TEXT NOT NULL UNIQUE,
            serving_qty TEXT,
            serving_unit TEXT,
            serving_weight_grams REAL,
            calories REAL,
            fat REAL,
            saturated_fat REAL,
            cholesterol REAL,
            sodium REAL,
            carbs REAL,
            fiber REAL,
            sugars REAL,
            protein REAL,
            potassium REAL,
            match_type TEXT,
            approved INTEGER
        )
        """
    )

    # ``recipes`` table stores high level recipe info.  We only
    # create it if it doesn't already exist so existing data is
    # preserved.
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY,
            recipe_title TEXT NOT NULL,
            version TEXT,
            source_url TEXT
        )
        """
    )

    # ``ingredients`` table stores the raw ingredient text and any
    # parsed information.  Again we create it only if needed.
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            food_name TEXT NOT NULL,
            quantity REAL,
            unit TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipes(id)
        )
        """
    )

    conn.commit()

def save_recipe_and_ingredients(recipe_data: dict, db_path="food_info.db") -> int:
    # Helper used by the scraping utilities to store a new recipe
    # and its ingredient list in the database.
    conn = get_connection(Path(db_path))
    cur = conn.cursor()

    # Insert into ``recipes`` table and get the new recipe ID
    cur.execute(
        "INSERT INTO recipes (recipe_title, version, source_url) VALUES (?, ?, ?)",
        (recipe_data.get("title"), None, recipe_data.get("url")),
    )
    recipe_id = cur.lastrowid

    # Insert each ingredient associated with the recipe
    for ingredient in recipe_data.get("ingredients", []):
        cur.execute(
            "INSERT INTO ingredients (recipe_id, food_name) VALUES (?, ?)",
            (recipe_id, ingredient),
        )

    # Finalize changes and return the new recipe ID to the caller
    conn.commit()
    conn.close()
    return recipe_id
