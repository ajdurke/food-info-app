import os
import sqlite3
from typing import Optional, Dict, Any
import requests
from dotenv import load_dotenv

from .sqlite_connector import get_connection
from food_project.processing.normalization import normalize_food_name

# -----------------------------------------
# 🔐 Load Nutritionix API credentials
# -----------------------------------------
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
    1. Normalize the food name
    2. Look up in DB by normalized_name
    3. If not present, call Nutritionix API
    4. Insert result into DB (safely)
    5. Return data
    """
    normalized = normalize_food_name(food_name)

    created = False
    if conn is None:
        conn = get_connection()
        created = True

    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # ✅ Ensure table exists, but don’t wipe it
    cur.execute("""
        CREATE TABLE IF NOT EXISTS food_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_name TEXT NOT NULL,
            normalized_name TEXT NOT NULL UNIQUE,
            serving_qty TEXT,
            serving_unit TEXT,
            serving_weight_grams REAL,
            calories REAL,
            fat REAL,
            saturated_fat REAL,
            cholesterol REAL,
            sodium REAL,
            carbs REAL,
            fiber REAL,
            sugars REAL,
            protein REAL,
            potassium REAL,
            match_type TEXT,
            approved INTEGER
        )
    """)

    cur.execute("SELECT * FROM food_info WHERE normalized_name = ?", (normalized,))
    row = cur.fetchone()
    if row:
        return dict(zip(row.keys(), row))  # ✅ Already in DB

    # 🚫 If not found, hit Nutritionix API
    try:
        print(f"⚠️ Mocking Nutritionix API for '{food_name}'")  # You can replace this with `_fetch_from_api()` to use the real API
        fetched = {
            "food_name": food_name,
            "serving_qty": 1,
            "serving_unit": "mock_unit",
            "serving_weight_grams": 100,
            "nf_calories": 0,
            "nf_total_fat": 0,
            "nf_saturated_fat": 0,
            "nf_cholesterol": 0,
            "nf_sodium": 0,
            "nf_total_carbohydrate": 0,
            "nf_dietary_fiber": 0,
            "nf_sugars": 0,
            "nf_protein": 0,
            "nf_potassium": 0,
        }
        # fetched = _fetch_from_api(food_name)  # ← uncomment to use real API
    except Exception as e:
        print(f"❌ API fetch failed for '{food_name}': {e}")
        return None

    # Insert into DB
    try:
        with conn:
            conn.execute("""
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
        print(f"💾 Committed: {normalized}")
    except Exception as e:
        print(f"❌ Failed to insert '{food_name}' into DB: {e}")
        return None

    cur.execute("SELECT * FROM food_info WHERE normalized_name = ?", (normalized,))
    row = cur.fetchone()
    result = dict(zip(row.keys(), row)) if row else None

    if created:
        conn.close()

    return result
