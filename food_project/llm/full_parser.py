"""LLM fallback parser using Together API with prompt templating and usage limits."""

import re
from pathlib import Path
from dotenv import load_dotenv
import os
import streamlit as st
from together import Together

# -------------------------------
# ✅ Load environment and config
# -------------------------------
load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY") or st.secrets["together"]["api_key"]


CACHE_PATH = Path("llm_full_parser_cache.json")
USAGE_LOG = Path("together_llm_usage.json")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
DAILY_LIMIT = 100

print("🔍 DEBUG Together API key loaded:", TOGETHER_API_KEY)

client = Together(api_key=TOGETHER_API_KEY)


# ----------------------------
# Helpers
# ----------------------------
def extract_json_block(text: str) -> str:
    """Remove markdown-style wrappers and isolate raw JSON block."""
    match = re.search(r"{[\s\S]*?}", text)
    return match.group(0) if match else text.strip()


def read_cache():
    return json.loads(CACHE_PATH.read_text()) if CACHE_PATH.exists() else {}


def write_cache(cache):
    CACHE_PATH.write_text(json.dumps(cache, indent=2))


def read_usage():
    return json.loads(USAGE_LOG.read_text()) if USAGE_LOG.exists() else {"count": 0}


def write_usage(usage):
    USAGE_LOG.write_text(json.dumps(usage, indent=2))


# ----------------------------
# Core Function
# ----------------------------
def parse_with_llm(raw_text: str, mock=False) -> dict:
    cache = read_cache()
    if raw_text in cache:
        return cache[raw_text]

    api_key = os.getenv("TOGETHER_API_KEY")  # recheck in case .env changed
    if mock or not api_key:
        print(f"⚠️ LLM fallback to mock mode (mock={mock}, key_set={bool(api_key)})")
        result = {
            "food": "mocked chicken",
            "amount": 3,
            "unit": "count",
            "normalized_name": "chicken",
            "food_score": 90,
            "unit_score": 95,
        }
        cache[raw_text] = result
        write_cache(cache)
        return result

    usage = read_usage()
    if usage["count"] >= DAILY_LIMIT:
        print("🚫 Together API daily limit reached. Using fallback.")
        return {"food": None, "amount": None, "unit": None, "normalized_name": None}

    # Compose prompt
    prompt = f"""
Extract structured ingredient data from the input text.

Return *only* valid JSON — no explanation, no formatting, no markdown, no backticks.

Example output format:
{{
  "food": "carrot",
  "amount": 2,
  "unit": "count",
  "normalized_name": "carrot",
  "food_score": 0.95,
  "unit_score": 1.0
}}

Text to parse: "{raw_text}"
"""

    try:
        print("🚀 Calling Together API...")
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You extract clean, structured data from messy ingredient strings."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=200,
        )
        print("📨 Raw response object:", json.dumps(response.model_dump(), indent=2))

        text = response.choices[0].message.content.strip()
        if not text:
            print("⚠️ LLM returned empty string.")
            return {"food": None, "amount": None, "unit": None, "normalized_name": None}

        cleaned = extract_json_block(text)
        try:
            parsed = json.loads(cleaned)
        except Exception as e:
            print("❌ JSON parsing failed:", e)
            print("🔎 Raw text that failed to parse:", repr(text))
            return {"food": None, "amount": None, "unit": None, "normalized_name": None}

    except Exception as e:
        print("❌ LLM call failed:", e)
        traceback.print_exc()
        return {"food": None, "amount": None, "unit": None, "normalized_name": None}

    cache[raw_text] = parsed
    usage["count"] += 1
    write_cache(cache)
    write_usage(usage)
    return parsed
