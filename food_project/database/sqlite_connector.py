import sqlite3
from pathlib import Path

DB_PATH = Path("data/food_info.db")

def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Return a connection to the SQLite database."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(conn: sqlite3.Connection) -> None:
    """Drop and recreate food_info table; ensure other tables exist."""
    cur = conn.cursor()

    # Recreate food_info table from scratch
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

    # Recipes table (preserve if already exists)
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

    # Ingredients table (preserve if already exists)
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
