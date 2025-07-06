import requests
import os
import streamlit as st

# Try Streamlit secrets first, then fallback to env variable
HF_API_KEY = st.secrets.get("huggingface", {}).get("api_key") or os.getenv("HF_API_KEY")

if not HF_API_KEY:
    raise Exception("❌ Hugging Face API key not found. Add to secrets.toml or set HF_API_KEY env var.")

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

def suggest_normalized_name(raw_ingredient: str, current_normalized: str, food_info_list: list[str]) -> str:
    prompt = f"""
You are helping clean ingredient names.

Raw ingredient: "{raw_ingredient}"
Current normalized: "{current_normalized}"
Available food options: {', '.join(food_info_list[:30])}...

Suggest a cleaner normalized name (e.g. just "parsley" instead of "flat-leaf parsley roughly") that would best match a real food entry.
Respond only with the name.
"""

    response = requests.post(API_URL, headers=HEADERS, json={
        "inputs": prompt,
        "parameters": {"max_new_tokens": 50, "temperature": 0.3}
    })

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return None

    result = response.json()
    if isinstance(result, list):
        return result[0]["generated_text"].split("\n")[-1].strip()
    else:
        return None
