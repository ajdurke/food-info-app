import os
from dotenv import load_dotenv
load_dotenv()  # ⬅️ Loads variables from .env if present

from food_project.llm.ingredient_name_reviewer import suggest_normalized_name

# Test values
raw_ingredient = "1 tbsp roughly chopped flat-leaf parsley"
current_normalized = "flat-leaf parsley roughly"
existing_options = [
    "parsley", "parsley leaves", "cilantro", "mint", "thyme", "oregano", "basil"
]

suggestion = suggest_normalized_name(raw_ingredient, current_normalized, existing_options)

print("🧠 LLM Suggestion:", suggestion)

