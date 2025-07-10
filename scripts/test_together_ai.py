# scripts/test_together_ai.py

import os
from dotenv import load_dotenv
from together import Together

load_dotenv()
api_key = os.getenv("TOGETHER_API_KEY")

client = Together(api_key=api_key)

response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    messages=[
        {"role": "system", "content": "You are a helpful assistant that cleans up messy ingredient names."},
        {"role": "user", "content": "Clean this ingredient name: 'bone-in chicken thighs, skinless, chopped'. Return only the core ingredient name without descriptors or preparation"},
    ],
    temperature=0.3,
    max_tokens=50,
)

print("🧠 Response:", response.choices[0].message.content.strip())


