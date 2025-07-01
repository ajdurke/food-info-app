import os
import sqlite3
from typing import Optional, Dict, Any
import requests
from dotenv import load_dotenv

from .sqlite_connector import get_connection, init_db
from food_project.processing.normalization import normalize_food_name

# -----------------------------------------
# 🔐 Load Nutritionix API credentials
# -----------------------------------------
# Tries to load from Streamlit first (if used there), otherwise from .env file

try:
    import streamlit as st
    NUTRITIONIX_APP_ID = st.secrets["nutritionix"]["app_id"]
    NUTRITIONIX_API_KEY = st.secrets["nutritionix"]["api_key"]
except:
    load_dotenv()
    NUTRITIONIX_APP_ID = os.getenv("NUTRITIONIX_APP_ID")
    NUTRITIONIX_API_KEY = os.getenv("NUTRITIONIX_API_KEY")

if not NUTRITIONIX_APP_ID or not NUTRITIONIX_API_KEY:
    raise Exception("❌ Nutritionix credentials not set.")

API_URL = "https://trackapi.nutritionix.com/v2/natural/nutrients"

# -----------------------------------------
# 🌐 Make request to Nutritionix API
# -----------------------------------------
def _fetch_from_api(query: str) -> Dict[str, Any]:
    headers = {
        "x-app-id": NUTRITIONIX_APP_ID,
        "x-app-key": NUTRITIONIX_API_KEY,
    }
    response = requests.post(API_URL, json={"query": query}, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()["foods"][0]

# -----------------------------------------
# 🍽 Main function to get nutrition data
# -----------------------------------------
def get_nutrition_data(food_name: str, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
    """
    This function does 4 things:
    1. Normalize the food name (e.g., "apples" -> "apple")
    2. Check if it's already in the food_info table
    3. If not, call the Nutritionix API to get nutrition data
    4. Save the result to the food_info table and return it
    """
    normalized = normalize_food_name(food_name)

    # Use passed-in connection or create a new one
    created = False
    if conn is None:
        conn = get_connection()
        created = True

    conn.row_factory = sqlite3.Row
    init_db(conn)  # Ensure tables exist

    cur = conn.cursor()

    # Check if this food is already in the DB
    cur.execute("SELECT * FROM food_info WHERE normalized_name = ?", (normalized,))
    row = cur.fetchone()
    if row:
        return dict(zip(row.keys(), row))  # ✅ Already exists

    # Otherwise fetch from Nutritionix API
    try:
        fetched = _fetch_from_api(food_name)
    except Exception as e:
        print(f"❌ API fetch failed for '{food_name}': {e}")
        return None

    # Insert into DB using normalized name from input
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO food_info (
                raw_name, normalized_name, serving_qty, serving_unit,
                serving_weight_grams, calories, fat, saturated_fat, cholesterol,
                sodium, carbs, fiber, sugars, protein, potassium
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            food_name,
            normalized,
            fetched.get("serving_qty"),
            fetched.get("serving_unit"),
            fetched.get("serving_weight_grams"),
            fetched.get("nf_calories"),
            fetched.get("nf_total_fat"),
            fetched.get("nf_saturated_fat"),
            fetched.get("nf_cholesterol"),
            fetched.get("nf_sodium"),
            fetched.get("nf_total_carbohydrate"),
            fetched.get("nf_dietary_fiber"),
            fetched.get("nf_sugars"),
            fetched.get("nf_protein"),
            fetched.get("nf_potassium"),
        ))
        conn.commit()
        print(f"💾 Committed: {normalized}")

    except Exception as e:
        print(f"❌ Failed to insert '{food_name}' into DB: {e}")
        return None


    # Re-query and return
    cur.execute("SELECT * FROM food_info WHERE normalized_name = ?", (normalized,))
    row = cur.fetchone()
    result = dict(zip(row.keys(), row)) if row else None

    if created:
        conn.close()

    return result
