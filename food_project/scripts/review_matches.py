import sqlite3

DB_PATH = "food_info.db"

def review_matches():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Get ingredients with fuzzy matches
    fuzzy_matches = cur.execute("""
        SELECT i.id, i.name AS raw_name, i.normalized_name, i.fuzz_score, f.normalized_name AS matched_food
        FROM ingredients i
        JOIN food_info f ON i.matched_food_id = f.id
        WHERE i.match_type = 'fuzzy'
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

        choice = input("Your choice: ").strip().lower()

        if choice == "y":
            print("✅ Approved.")
            continue

        elif choice == "n":
            cur.execute("""
                UPDATE ingredients
                SET matched_food_id = NULL, match_type = NULL, fuzz_score = NULL
                WHERE id = ?
            """, (row["id"],))
            print("❌ Match removed.")

        elif choice == "m":
            new_match = input("Enter new food_info.normalized_name: ").strip().lower()
            match_row = cur.execute("SELECT id FROM food_info WHERE normalized_name = ?", (new_match,)).fetchone()
            if match_row:
                cur.execute("""
                    UPDATE ingredients
                    SET matched_food_id = ?, match_type = 'manual', fuzz_score = 100
                    WHERE id = ?
                """, (match_row["id"], row["id"]))
                print("✏️ Manually overridden.")
            else:
                print("⚠️ No such normalized_name found in food_info.")

        else:
            print("⏭️ Skipped.")

    conn.commit()
    conn.close()
    print("\n🎉 Done reviewing fuzzy matches.")

if __name__ == "__main__":
    review_matches()
