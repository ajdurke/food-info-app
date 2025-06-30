import argparse
import sqlite3


def review(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM food_info WHERE approved IS NULL ORDER BY match_type")
    rows = cur.fetchall()
    for row in rows:
        print("\n=== {} (match: {}) ===".format(row["raw_name"], row["match_type"]))
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Review pending Nutritionix matches")
    parser.add_argument("--db", default="food_info.db", help="SQLite database path")
    args = parser.parse_args()
    review(args.db)


if __name__ == "__main__":
    main()

