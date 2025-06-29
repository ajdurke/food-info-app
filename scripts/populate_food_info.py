# populate_food_info.py

import sqlite3
from food_project.database.sqlite_connector import get_connection
from food_project.helpers.nutritionix_service import fetch_food_matches
import json

DELETE_EXISTING = False  # Set True to clear existing data first
FOOD_LIST = [
    "apple,"
    "banana,"
    "orange,"
    "grape,"
    "watermelon,"
    "strawberry,"
    "blueberry,"
    "raspberry,"
    "blackberry,"
    "kiwi,"
    "pineapple,"
    "mango,"
    "papaya,"
    "peach,"
    "pear,"
    "plum,"
    "cherry,"
    "lemon,"
    "lime,"
    "cantaloupe,"
    "honeydew,"
    "grapefruit,"
    "apricot,"
    "pomegranate,"
    "fig,"
    "guava,"
    "date,"
    "coconut,"
    "carrot,"
    "broccoli,"
    "cauliflower,"
    "spinach,"
    "kale,"
    "lettuce,"
    "romaine,"
    "arugula,"
    "zucchini,"
    "squash,"
    "cucumber,"
    "celery,"
    "bell pepper,"
    "onion,"
    "garlic,"
    "ginger,"
    "green beans,"
    "snap peas,"
    "edamame,"
    "okra,"
    "sweet potato,"
    "potato,"
    "yam,"
    "beet,"
    "radish,"
    "turnip,"
    "parsnip,"
    "leek,"
    "asparagus,"
    "mushroom,"
    "artichoke,"
    "brussels sprouts,"
    "eggplant,"
    "tomato,"
    "corn,"
    "pumpkin,"
    "chili pepper,"
    "chicken breast,"
    "chicken thigh,"
    "ground beef,"
    "steak,"
    "pork chop,"
    "bacon,"
    "ham,"
    "turkey breast,"
    "sausage,"
    "hot dog,"
    "pepperoni,"
    "salami,"
    "lamb,"
    "duck,"
    "venison,"
    "shrimp,"
    "salmon,"
    "tuna,"
    "cod,"
    "tilapia,"
    "catfish,"
    "trout,"
    "mackerel,"
    "sardines,"
    "crab,"
    "lobster,"
    "scallops,"
    "oysters,"
    "clams,"
    "white rice,"
    "brown rice,"
    "quinoa,"
    "oats,"
    "barley,"
    "farro,"
    "bulgur,"
    "couscous,"
    "bread,"
    "whole wheat bread,"
    "white bread,"
    "rye bread,"
    "bagel,"
    "english muffin,"
    "tortilla,"
    "corn tortilla,"
    "flour tortilla,"
    "pita,"
    "naan,"
    "crackers,"
    "pasta,"
    "spaghetti,"
    "macaroni,"
    "noodles,"
    "ramen,"
    "soba noodles,"
    "udon,"
    "lentils,"
    "chickpeas,"
    "black beans,"
    "kidney beans,"
    "pinto beans,"
    "soybeans,"
    "navy beans,"
    "peas,"
    "tofu,"
    "whole milk,"
    "lowfat milk,"
    "skim milk,"
    "almond milk,"
    "soy milk,"
    "oat milk,"
    "yogurt,"
    "greek yogurt,"
    "cheddar cheese,"
    "mozzarella cheese,"
    "parmesan cheese,"
    "ricotta,"
    "cream cheese,"
    "butter,"
    "margarine,"
    "ice cream,"
    "whipped cream,"
    "half and half,"
    "sour cream,"
    "egg,"
    "egg white,"
    "egg yolk,"
    "olive oil,"
    "canola oil,"
    "vegetable oil,"
    "coconut oil,"
    "avocado oil,"
    "shortening,"
    "lard,"
    "mayonnaise,"
    "dark chocolate,"
    "milk chocolate,"
    "chips,"
    "pretzels,"
    "ketchup,"
    "mustard,"
    "ranch dressing,"
    "vinaigrette,"
    "caesar dressing,"
    "soy sauce,"
    "sriracha,"
    "hot sauce,"
    "barbecue sauce,"
    "honey mustard,"
    "buffalo sauce,"
    "teriyaki sauce,"
    "tahini,"
    "hummus,"
    "salsa,"
    "guacamole,"
    "relish,"
    "gravy,"
    "pesto,"
    "kimchi,"
    "falafel,"
    "tabbouleh,"
    "tzatziki,"
    "plantain,"
    "cassava,"
    "yuca,"
    "fufu,"
    "injera,"
    "jollof rice,"
    "coffee,"
    "black tea,"
    "green tea,"
    "cola,"
    "orange juice,"
    "apple juice,"
    "grape juice,"
    "lemonade,"
    "salt,"
    "black pepper,"
    "sugar,"
    "brown sugar,"
    "honey,"
    "maple syrup,"
    "molasses,"
    "baking soda,"
    "baking powder,"
    "cornstarch,"
    "yeast,"
    "flour,"
    "whole wheat flour,"
    "all-purpose flour,"
    "gluten-free flour,"
    "spaghetti squash,"
    "acorn squash,"
    "butternut squash,"
    "cabbage,"
    "bok choy,"
    "collard greens,"
    "swiss chard,"
    "turnip greens,"
    "mustard greens,"
    "watercress,"
    "endive,"
    "radicchio,"
    "cress,"
    "arctic char,"
    "halibut,"
    "sea bass,"
    "tilapia,"
    "pollock,"
    "mullet,"
    "anchovy,"
    "caviar,"
    "seaweed,"
    "nori,"
    "kombu,"
    "wakame,"
    "kelp,"
    "spirulina,"
    "chlorella,"
    "chia seeds,"
    "flaxseeds,"
    "pumpkin seeds,"
    "sunflower seeds,"
    "safflower seeds,"
    "sesame seeds,"
    "hemp seeds,"
    "poppy seeds,"
    "caraway seeds,"
    "cumin seeds,"
    "fennel seeds,"
    "coriander seeds,"
    "coconut milk,"
    "almond butter,"
    "peanut butter,"
    "cashew butter,"
    "hazelnut spread,"
    "sunflower seed butter,"
    "tahini paste,"
    "nutella,"
    "granola,"
    "muesli,"
    "corn chips,"
    "tortilla chips,"
    "pita chips,"
    "veggie chips,"
]

def clear_existing_data(conn):
    with conn:
        conn.execute("DELETE FROM food_info")

def already_exists(conn, normalized_name):
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM food_info WHERE normalized_name = ?", (normalized_name,))
    return cursor.fetchone() is not None

def insert_entry(conn, food_data, match_type):
    food_data["match_type"] = match_type  # either "exact", "next_best", or "related"
    with conn:
        conn.execute("""
            INSERT INTO food_info (
                raw_name, normalized_name, serving_qty, serving_unit,
                serving_weight_grams, calories, fat, saturated_fat, cholesterol,
                sodium, carbs, fiber, sugars, protein, potassium, match_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            food_data.get("raw_name"),
            food_data.get("normalized_name"),
            food_data.get("serving_qty"),
            food_data.get("serving_unit"),
            food_data.get("serving_weight_grams"),
            food_data.get("calories"),
            food_data.get("fat"),
            food_data.get("saturated_fat"),
            food_data.get("cholesterol"),
            food_data.get("sodium"),
            food_data.get("carbs"),
            food_data.get("fiber"),
            food_data.get("sugars"),
            food_data.get("protein"),
            food_data.get("potassium"),
            match_type
        ))

def run():
    conn = get_connection()
    if DELETE_EXISTING:
        clear_existing_data(conn)

    for food_name in FOOD_LIST:
        print(f"\nFetching matches for: {food_name}")
        exact, next_best, others = fetch_food_matches(food_name)

        if exact and not already_exists(conn, exact["normalized_name"]):
            insert_entry(conn, exact, "exact")

        if next_best and not already_exists(conn, next_best["normalized_name"]):
            insert_entry(conn, next_best, "next_best")

        for alt in others:
            if not already_exists(conn, alt["normalized_name"]):
                insert_entry(conn, alt, "related")

if __name__ == "__main__":
    run()
