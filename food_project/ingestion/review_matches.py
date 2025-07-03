"""Console workflow for manually reviewing ingredient matches."""

import argparse
from food_project.database.sqlite_connector import get_connection, init_db
from pathlib import Path

def review_matches(db_path: str, init: bool = False) -> None:
    """Walk through unmatched ingredients and approve or reject matches."""
    conn = get_connection(Path(db_path))
    if init:
        print("⚙️ init_db() is recreating the food_info table")
        init_db(conn)

    cur = conn.cursor()

    # Ensure our table has columns to track the review status
    for col_def in [
        "ALTER TABLE ingredients ADD COLUMN match_reviewed BOOLEAN",
        "ALTER TABLE ingredients ADD COLUMN review_outcome TEXT"
    ]:
        try:
            cur.execute(col_def)
        except Exception:
            pass  # Ignore if column already exists

    # Load any ingredients that were auto-matched using fuzzy logic
    fuzzy_matches = cur.execute("""
        SELECT i.id, i.food_name AS raw_name, i.normalized_name, i.fuzz_score, f.normalized_name AS matched_food
        FROM ingredients i
        JOIN food_info f ON i.matched_food_id = f.id
        WHERE i.match_type = 'fuzzy' AND (i.match_reviewed IS NULL OR i.match_reviewed = 0)
    """).fetchall()

    if not fuzzy_matches:
        print("✅ No fuzzy matches to review.")
        return

    for row in fuzzy_matches:
        print("\n----------------------------")
        print(f"Ingredient:        {row['raw_name']}")
        print(f"Normalized Name:   {row['normalized_name']}")
        print(f"Matched to:        {row['matched_food']}")
        print(f"Fuzz Score:        {row['fuzz_score']}")
        print("----------------------------")
        print("Options: [y]es (approve), [n]o (reject), [m]anual override, [s]kip")

        # Prompt the reviewer for a decision
        choice = input("Your choice: ").strip().lower()

        if choice == "y":
            cur.execute("""
                UPDATE ingredients
                SET match_reviewed = 1, review_outcome = 'approved'
                WHERE id = ?
            """, (row["id"],))
            print("✅ Approved.")

        elif choice == "n":
            cur.execute("""
                UPDATE ingredients
                SET matched_food_id = NULL,
                    match_type = NULL,
                    fuzz_score = NULL,
                    match_reviewed = 1,
                    review_outcome = 'rejected'
                WHERE id = ?
            """, (row["id"],))
            print("❌ Match removed.")

        elif choice == "m":
            # Let the reviewer manually specify the correct normalized name
            new_match = input("Enter new food_info.normalized_name: ").strip().lower()
            match_row = cur.execute("SELECT id FROM food_info WHERE normalized_name = ?", (new_match,)).fetchone()
            if match_row:
                cur.execute("""
                    UPDATE ingredients
                    SET matched_food_id = ?, match_type = 'manual', fuzz_score = 100,
                        match_reviewed = 1, review_outcome = 'manual'
                    WHERE id = ?
                """, (match_row["id"], row["id"]))
                print("✏️ Manually overridden.")
            else:
                print("⚠️ No such normalized_name found in food_info.")

        else:
            cur.execute("""
                UPDATE ingredients
                SET match_reviewed = 1, review_outcome = 'skipped'
                WHERE id = ?
            """, (row["id"],))
            print("⏭️ Skipped.")

    conn.commit()
    conn.close()
    print("\n🎉 Done reviewing fuzzy matches.")

def main():
    # Simple command line wrapper around ``review_matches``
    parser = argparse.ArgumentParser(description="Review fuzzy matches between ingredients and food_info.")
    parser.add_argument("--db", default="food_info.db", help="SQLite database path")
    parser.add_argument("--init", action="store_true", help="Recreate food_info table (destructive)")
    args = parser.parse_args()
    review_matches(db_path=args.db, init=args.init)

if __name__ == "__main__":
    main()
