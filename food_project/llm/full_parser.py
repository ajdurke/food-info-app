"""LLM fallback parser using Together API with prompt templating and usage limits."""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from together import Together

load_dotenv()

CACHE_PATH = Path("llm_full_parser_cache.json")
USAGE_LOG = Path("together_llm_usage.json")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
DAILY_LIMIT = 100  # Max allowed calls per day

client = Together(api_key=TOGETHER_API_KEY)

def read_cache():
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text())
    return {}

def write_cache(cache):
    CACHE_PATH.write_text(json.dumps(cache, indent=2))

def read_usage():
    if USAGE_LOG.exists():
        return json.loads(USAGE_LOG.read_text())
    return {"count": 0}

def write_usage(usage):
    USAGE_LOG.write_text(json.dumps(usage, indent=2))

def parse_with_llm(raw_text: str, mock=False) -> dict:
    cache = read_cache()
    if raw_text in cache:
        return cache[raw_text]

    if mock or not TOGETHER_API_KEY:
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

    prompt = f"""
You are a helpful assistant that extracts structured ingredient information.

Extract the following from this text:
- Core ingredient name (cleaned, e.g., "parsley")
- Amount (numeric or decimal)
- Unit (e.g., "tbsp", "cup", or "count")
Respond in this JSON format:
{{"food": ..., "amount": ..., "unit": ..., "normalized_name": ..., "food_score": ..., "unit_score": ...}}

Input: "{raw_text}"
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You extract clean, structured data from messy ingredient strings."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=200,
        )
        text = response.choices[0].message.content.strip()
        parsed = json.loads(text)
    except Exception as e:
        print("❌ LLM call failed:", e)
        return {"food": None, "amount": None, "unit": None, "normalized_name": None}

    cache[raw_text] = parsed
    usage["count"] += 1
    write_cache(cache)
    write_usage(usage)

    return parsed
