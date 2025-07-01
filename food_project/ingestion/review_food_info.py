import argparse
from pathlib import Path
from food_project.database.sqlite_connector import get_connection, init_db

def review_food_info(db_path: str, init: bool = False) -> None:
    if init:
        print("⚙️ init_db() is recreating the food_info table")
    conn = get_connection(Path(db_path))
    if init:
        init_db(conn)

    cur = conn.cursor()
    cur.execute("SELECT * FROM food_info WHERE approved IS NULL ORDER BY match_type")
    rows = cur.fetchall()

    if not rows:
        print("✅ No unapproved food entries to review.")
        return

    for row in rows:
        print(f"\n=== {row['raw_name']} (match: {row['match_type']}) ===")
        for key in row.keys():
            if key in {"id", "raw_name", "normalized_name", "match_type", "approved"}:
                continue
            print(f"{key}: {row[key]}")
        ans = input("Approve this entry? [y/n/skip]: ").strip().lower()
        if ans == "y":
            cur.execute("UPDATE food_info SET approved=1 WHERE id=?", (row["id"],))
        elif ans == "n":
            cur.execute("UPDATE food_info SET approved=0 WHERE id=?", (row["id"],))

    conn.commit()
    conn.close()
    print("🎉 Done reviewing food_info entries.")

def main():
    parser = argparse.ArgumentParser(description="Review pending Nutritionix entries in food_info.")
    parser.add_argument("--db", default="food_info.db", help="SQLite database path")
    parser.add_argument("--init", action="store_true", help="Recreate food_info table (destructive)")
    args = parser.parse_args()
    review_food_info(db_path=args.db, init=args.init)

if __name__ == "__main__":
    main()
