"""Interface for fetching nutrition data from the Nutritionix API."""

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
    foods = response.json().get("foods", [])
    if not foods:
        raise ValueError(f"No foods returned for query: '{query}'")
    return foods[0]

# -----------------------------------------
# 🍽 Main function to get nutrition data
# -----------------------------------------
def get_nutrition_data(
    food_name: str,
    conn: Optional[sqlite3.Connection] = None,
    use_mock: bool = False,
    skip_if_exists: bool = False
) -> Optional[Dict[str, Any]]:
    normalized = normalize_food_name(food_name)

    created = False
    if conn is None:
        conn = get_connection()
        created = True

    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Initial existence check
    cur.execute("SELECT * FROM food_info WHERE normalized_name = ?", (normalized,))
    row = cur.fetchone()

    if skip_if_exists and row:
        print(f"⏩ Skipped (already exists in DB): {normalized}")
        return None

    if row:
        return dict(zip(row.keys(), row))

    if use_mock:
        print(f"⚠️ Mocking Nutritionix API for '{food_name}'")
        mock_data = {
            "food_name": food_name,
            "serving_qty": 100,
            "serving_unit": "g",
            "serving_weight_grams": 100,
            "nf_calories": 100,
            "nf_total_fat": 1,
            "nf_saturated_fat": 0.2,
            "nf_cholesterol": 0,
            "nf_sodium": 10,
            "nf_total_carbohydrate": 20,
            "nf_dietary_fiber": 3,
            "nf_sugars": 15,
            "nf_protein": 1,
            "nf_potassium": 200,
        }
    else:
        try:
            mock_data = _fetch_from_api(food_name)
        except Exception as e:
            print(f"❌ API fetch failed for '{food_name}': {e}")
            return None

    norm = normalize_food_name(mock_data["food_name"])

    # Final check before insert
    cur.execute("SELECT id FROM food_info WHERE normalized_name = ?", (norm,))
    if cur.fetchone():
        print(f"⚠️ Already exists just before insert: {norm}")
        return None

    with conn:
        conn.execute("""
            INSERT INTO food_info (
                raw_name, normalized_name, serving_qty, serving_unit,
                serving_weight_grams, calories, fat, saturated_fat, cholesterol,
                sodium, carbs, fiber, sugars, protein, potassium
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            food_name,
            norm,
            mock_data.get("serving_qty"),
            mock_data.get("serving_unit"),
            mock_data.get("serving_weight_grams"),
            mock_data.get("nf_calories"),
            mock_data.get("nf_total_fat"),
            mock_data.get("nf_saturated_fat"),
            mock_data.get("nf_cholesterol"),
            mock_data.get("nf_sodium"),
            mock_data.get("nf_total_carbohydrate"),
            mock_data.get("nf_dietary_fiber"),
            mock_data.get("nf_sugars"),
            mock_data.get("nf_protein"),
            mock_data.get("nf_potassium"),
        ))

    cur.execute("SELECT * FROM food_info WHERE normalized_name = ?", (norm,))
    row = cur.fetchone()
    result = dict(zip(row.keys(), row)) if row else None

    if created:
        conn.close()

    return result
