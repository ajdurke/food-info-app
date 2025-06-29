# scripts/create_fake_food_info.py

import sqlite3

fake_foods = [
    {
        "raw_name": "carrots",
        "normalized_name": "carrot",
        "serving_qty": "100",
        "serving_unit": "g",
        "serving_weight_grams": 100,
        "calories": 41,
        "fat": 0.2,
        "saturated_fat": 0.0,
        "cholesterol": 0,
        "sodium": 69,
        "carbs": 10,
        "fiber": 2.8,
        "sugars": 4.7,
        "protein": 0.9,
        "potassium": 320,
        "match_type": "manual_fake",
        "approved": 1,
    },
    {
        "raw_name": "shredded cheddar cheese",
        "normalized_name": "cheddar cheese",
        "serving_qty": "28",
        "serving_unit": "g",
        "serving_weight_grams": 28,
        "calories": 113,
        "fat": 9.4,
        "saturated_fat": 6,
        "cholesterol": 30,
        "sodium": 180,
        "carbs": 0.4,
        "fiber": 0,
        "sugars": 0.1,
        "protein": 7,
        "potassium": 20,
        "match_type": "manual_fake",
        "approved": 1,
    },
    {
        "raw_name": "chicken breast",
        "normalized_name": "chicken breast",
        "serving_qty": "100",
        "serving_unit": "g",
        "serving_weight_grams": 100,
        "calories": 165,
        "fat": 3.6,
        "saturated_fat": 1.0,
        "cholesterol": 85,
        "sodium": 74,
        "carbs": 0,
        "fiber": 0,
        "sugars": 0,
        "protein": 31,
        "potassium": 256,
        "match_type": "manual_fake",
        "approved": 1,
    },
    {
        "raw_name": "olive oil",
        "normalized_name": "olive oil",
        "serving_qty": "1",
        "serving_unit": "tbsp",
        "serving_weight_grams": 13.5,
        "calories": 119,
        "fat": 13.5,
        "saturated_fat": 2,
        "cholesterol": 0,
        "sodium": 0,
        "carbs": 0,
        "fiber": 0,
        "sugars": 0,
        "protein": 0,
        "potassium": 0,
        "match_type": "manual_fake",
        "approved": 1,
    },
    {
        "raw_name": "all-purpose flour",
        "normalized_name": "flour",
        "serving_qty": "100",
        "serving_unit": "g",
        "serving_weight_grams": 100,
        "calories": 364,
        "fat": 1,
        "saturated_fat": 0.2,
        "cholesterol": 0,
        "sodium": 2,
        "carbs": 76,
        "fiber": 2.7,
        "sugars": 0.3,
        "protein": 10,
        "potassium": 107,
        "match_type": "manual_fake",
        "approved": 1,
    },
]

def seed_fake_food_info(db_path="food_info.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for food in fake_foods:
        cursor.execute("""
            INSERT INTO food_info (
                name, raw_name, normalized_name, serving_qty, serving_unit,
                serving_weight_grams, calories, fat, saturated_fat, cholesterol,
                sodium, carbs, fiber, sugars, protein, potassium, match_type, approved
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            food["raw_name"],  # name
            food["raw_name"],
            food["normalized_name"],
            food["serving_qty"], food["serving_unit"], food["serving_weight_grams"],
            food["calories"], food["fat"], food["saturated_fat"], food["cholesterol"],
            food["sodium"], food["carbs"], food["fiber"], food["sugars"],
            food["protein"], food["potassium"], food["match_type"], food["approved"]
        ))

    conn.commit()
    conn.close()
    print("✅ Fake food data inserted into food_info.")

if __name__ == "__main__":
    seed_fake_food_info()
