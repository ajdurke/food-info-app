# import sqlite3

# # Connect to a new SQLite file (creates it if not found)
# conn = sqlite3.connect("food_info.db")
# cursor = conn.cursor()

# # Create a table for recipes
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS recipes (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     title TEXT NOT NULL,
#     version TEXT,
#     source_url TEXT
# )
# """)

# # Create a table for ingredients
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS ingredients (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     recipe_id INTEGER,
#     name TEXT NOT NULL,
#     amount REAL,
#     unit TEXT,
#     FOREIGN KEY (recipe_id) REFERENCES recipes (id)
# )
# """)

# # Insert sample data
# cursor.execute("INSERT INTO recipes (title, version, source_url) VALUES (?, ?, ?)",
#                ("Simple Pasta", "v1", "https://example.com/simple-pasta"))
# recipe_id = cursor.lastrowid

# cursor.executemany("INSERT INTO ingredients (recipe_id, name, amount, unit) VALUES (?, ?, ?, ?)", [
#     (recipe_id, "Pasta", 200, "g"),
#     (recipe_id, "Olive oil", 2, "tbsp"),
#     (recipe_id, "Garlic", 3, "cloves")
# ])

# # Save and close
# conn.commit()
# conn.close()

# print("food_info.db created with sample data.")
