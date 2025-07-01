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
    # When running within Streamlit we store API credentials in
    # ``.streamlit/secrets.toml`` for security.
    import streamlit as st
    NUTRITIONIX_APP_ID = st.secrets["nutritionix"]["app_id"]
    NUTRITIONIX_API_KEY = st.secrets["nutritionix"]["api_key"]
except:
    # Fallback for command line usage: read credentials from a
    # local ``.env`` file or environment variables.
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
    """Low-level helper that calls the Nutritionix REST API."""
    headers = {
        "x-app-id": NUTRITIONIX_APP_ID,
        "x-app-key": NUTRITIONIX_API_KEY,
    }
    # The API expects a POST request with the food name in the ``query`` field
    response = requests.post(API_URL, json={"query": query}, headers=headers, timeout=10)
    # ``raise_for_status`` will throw an error for HTTP failures
    response.raise_for_status()
    # Nutritionix returns a list of foods; we only care about the first one
    return response.json()["foods"][0]

# -----------------------------------------
# 🍽 Main function to get nutrition data
# -----------------------------------------
def get_nutrition_data(
    food_name: str,
    conn: Optional[sqlite3.Connection] = None,
    use_mock: bool = False,
    skip_if_exists: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Fetch and store nutrition data for a food item unless already present.

    Parameters:
        - food_name: str
        - conn: Optional SQLite connection
        - use_mock: Use mock data instead of API
        - skip_if_exists: Return existing data if present, skip API call and DB insert

    Returns:
        - dict of food data if successful or already present, None otherwise
    """
    # Normalize the name so that "Carrots" and "carrot" are treated the same
    normalized = normalize_food_name(food_name)

    # ``conn`` allows callers to reuse an existing database connection.
    created = False
    if conn is None:
        conn = get_connection()
        created = True

    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # If we already have this food in the database we can return it directly
    cur.execute("SELECT * FROM food_info WHERE normalized_name = ?", (normalized,))
    row = cur.fetchone()
    if row:
        if skip_if_exists:
            print(f"⏩ Skipped (already exists in DB): {normalized}")
        return dict(zip(row.keys(), row))

    # Optionally use mock data
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
            # Real API call
            mock_data = _fetch_from_api(food_name)
        except Exception as e:
            print(f"❌ API fetch failed for '{food_name}': {e}")
            return None

    # Insert the resulting nutrition info into the database
    norm = normalize_food_name(mock_data["food_name"])
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

    # Retrieve and return the stored row so callers receive a dictionary
    cur.execute("SELECT * FROM food_info WHERE normalized_name = ?", (norm,))
    row = cur.fetchone()
    result = dict(zip(row.keys(), row)) if row else None

    if created:
        # Close the connection we opened earlier
        conn.close()

    return result
