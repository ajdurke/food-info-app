import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
from food_project.database.nutritionix_service import get_nutrition_data

# 1. Connect to your local database
conn = sqlite3.connect("your_database_path_here.db")  # Update this if needed

# 2. Try a food you expect NOT to be in the DB
food_name = "cooked spinach"

print(f"\n🔍 Looking up '{food_name}'...")
result = get_nutrition_data(food_name, conn)

# 3. Print the result
if result:
    print("✅ Data returned:")
    for k, v in result.items():
        print(f"  {k}: {v}")
else:
    print("❌ No data found.")

# 4. Try it again (should hit local DB now)
print(f"\n🔁 Looking up '{food_name}' again...")
result2 = get_nutrition_data(food_name, conn)
