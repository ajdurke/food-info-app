import os
from dotenv import load_dotenv
import openai

# Load Together API key
load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
TOGETHER_BASE_URL = "https://api.together.xyz/v1"

if not TOGETHER_API_KEY:
    raise ValueError("❌ TOGETHER_API_KEY not found in environment variables.")

# Initialize Together OpenAI-compatible client
client = openai.OpenAI(
    api_key=TOGETHER_API_KEY,
    base_url=TOGETHER_BASE_URL
)

def call_together_ai(prompt: str, model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free") -> str:
    """
    Sends a prompt to Together.ai chat model and returns the response string.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that parses food ingredients."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()
