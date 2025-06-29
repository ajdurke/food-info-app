import os
import sqlite3
from typing import Optional, Dict, Any
import requests
from .sqlite_connector import get_connection, init_db

# Hybrid credential loading: first try Streamlit, then fallback to .env or system env vars
try:
    import streamlit as st
    NUTRITIONIX_APP_ID = st.secrets["nutritionix"]["app_id"]
    NUTRITIONIX_API_KEY = st.secrets["nutritionix"]["api_key"]
except Exception:
    from dotenv import load_dotenv
    load_dotenv()
    NUTRITIONIX_APP_ID = os.getenv("NUTRITIONIX_APP_ID")
    NUTRITIONIX_API_KEY = os.getenv("NUTRITIONIX_API_KEY")


if not NUTRITIONIX_APP_ID or not NUTRITIONIX_API_KEY:
    raise Exception("Nutritionix credentials not set in secrets.toml or .env")

API_URL = "https://trackapi.nutritionix.com/v2/natural/nutrients"


def normalize_food_name(name: str) -> str:
    if not name:
        return ""
    name = name.lower().strip()
    descriptors = {
        "fresh",
        "dried",
        "chopped",
        "sliced",
        "minced",
        "raw",
        "cooked",
        "shredded",
        "unsalted",
        "salted",
    }
    words = [w for w in name.split() if w not in descriptors]
    if words:
        last = words[-1]
        if last.endswith("es") and len(last) > 2:
            last = last[:-2]
        elif last.endswith("s") and len(last) > 1 and not last.endswith("ss"):
            last = last[:-1]
        words[-1] = last
    return " ".join(words)

def _fetch_from_api(query: str) -> Dict[str, Any]:
    if not NUTRITIONIX_APP_ID or not NUTRITIONIX_API_KEY:
        raise ValueError("Nutritionix credentials not set")
    headers = {
        "x-app-id": NUTRITIONIX_APP_ID,
        "x-app-key": NUTRITIONIX_API_KEY,
    }
    resp = requests.post(API_URL, json={"query": query}, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()["foods"][0]
    return {
        "serving_qty": data.get("serving_qty"),
        "serving_unit": data.get("serving_unit"),
        "serving_weight_grams": data.get("serving_weight_grams"),
        "calories": data.get("nf_calories"),
        "fat": data.get("nf_total_fat"),
        "saturated_fat": data.get("nf_saturated_fat"),
        "cholesterol": data.get("nf_cholesterol"),
        "sodium": data.get("nf_sodium"),
        "carbs": data.get("nf_total_carbohydrate"),
        "fiber": data.get("nf_dietary_fiber"),
        "sugars": data.get("nf_sugars"),
        "protein": data.get("nf_protein"),
        "potassium": data.get("nf_potassium"),
    }

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
        result = dict(row)
    else:
        try:
            fetched = _fetch_from_api(food_name)
        except Exception as e:
            print(f"API fetch failed: {e}")
            fetched = None

        if fetched:
            cur.execute(
                """
                INSERT INTO food_info (
                    raw_name, normalized_name, serving_qty, serving_unit,
                    serving_weight_grams, calories, fat, saturated_fat, cholesterol,
                    sodium, carbs, fiber, sugars, protein, potassium
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    food_name,
                    normalized,
                    fetched.get("serving_qty"),
                    fetched.get("serving_unit"),
                    fetched.get("serving_weight_grams"),
                    fetched.get("calories"),
                    fetched.get("fat"),
                    fetched.get("saturated_fat"),
                    fetched.get("cholesterol"),
                    fetched.get("sodium"),
                    fetched.get("carbs"),
                    fetched.get("fiber"),
                    fetched.get("sugars"),
                    fetched.get("protein"),
                    fetched.get("potassium"),
                ),
            )
            conn.commit()
            cur.execute("SELECT * FROM food_info WHERE normalized_name = ?", (normalized,))
            row = cur.fetchone()
            result = dict(row) if row else None
        else:
            result = None
    if created:
        conn.close()
    return result
