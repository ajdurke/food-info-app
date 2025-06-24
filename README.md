# Food Info App

This project originally stored data in Google Sheets. To allow offline use and more flexible queries, an SQLite backend is now available.

## Database Schema

The SQLite database uses two main tables instead of repeating recipe information for every ingredient:

```
recipes(
    id INTEGER PRIMARY KEY,
    recipe_title TEXT NOT NULL,
    version TEXT,
    source_url TEXT
)

ingredients(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id),
    food_name TEXT NOT NULL,
    quantity REAL,
    unit TEXT
)
```

`recipes` holds one row per recipe and `ingredients` references it via `recipe_id`.

## Migrating Data

Use `scripts/migrate_to_sqlite.py` to copy data directly from Google Sheets
into `data/food_info.db`:

```bash
python scripts/migrate_to_sqlite.py
```

The script expects the same Google credentials currently used by the app (via `streamlit.secrets`).

### Importing from CSV

If you have exported the **recipes** tab from Google Sheets as a CSV file you
can populate the SQLite database without network access:

```bash
python scripts/import_csv_to_sqlite.py path/to/recipes.csv
```

This command creates any missing tables and inserts one `recipes` row for each
`recipe_id` found in the CSV along with its ingredient rows.

