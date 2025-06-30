import os
import sqlite3
from typing import Optional, Dict, Any
import requests
from .sqlite_connector import get_connection, init_db
from food_project.utils.normalization import normalize_food_name
from dotenv import load_dotenv

try:
    import streamlit as st
    NUTRITIONIX_APP_ID = st.secrets["nutritionix"]["app_id"]
    NUTRITIONIX_API_KEY = st.secrets["nutritionix"]["api_key"]
except:
    load_dotenv()
    NUTRITIONIX_APP_ID = os.getenv("NUTRITIONIX_APP_ID")
    NUTRITIONIX_API_KEY = os.getenv("NUTRITIONIX_API_KEY")

if not NUTRITIONIX_APP_ID or not NUTRITIONIX_API_KEY:
    raise Exception("Nutritionix credentials not set.")

API_URL = "https://trackapi.nutritionix.com/v2/natural/nutrients"

def _fetch_from_api(query: str) -> Dict[str, Any]:
    headers = {
        "x-app-id": NUTRITIONIX_APP_ID,
        "x-app-key": NUTRITIONIX_API_KEY,
    }
    resp = requests.post(API_URL, json={"query": query}, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()["foods"][0]

def get_nutrition_data(food_name: str, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
    created = False
    if conn is None:
        conn = get_connection()
        created = True
    conn.row_factory = sqlite3.Row
    init_db(conn)

    normalized = normalize_food_name(food_name)
    cur = conn.cursor()
    cur.execute("SELECT * FROM food_info WHERE normalized_name = ?", (normalized,))
    row = cur.fetchone()
    if row:
        return dict(zip(row.keys(), row))

    try:
        fetched = _fetch_from_api(food_name)
    except Exception as e:
        print(f"API fetch failed: {e}")
        return None

    norm_from_api = normalize_food_name(fetched["food_name"])
    cur.execute("""
        INSERT INTO food_info (
            raw_name, normalized_name, serving_qty, serving_unit,
            serving_weight_grams, calories, fat, saturated_fat, cholesterol,
            sodium, carbs, fiber, sugars, protein, potassium
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        food_name,
        norm_from_api,
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

    cur.execute("SELECT * FROM food_info WHERE normalized_name = ?", (norm_from_api,))
    row = cur.fetchone()
    result = dict(zip(row.keys(), row)) if row else None

    if created:
        conn.close()
    return result
