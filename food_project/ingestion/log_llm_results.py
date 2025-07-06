"""Log logic and LLM results for later review."""

import sqlite3

def log_review_result(conn, ingredient_id, logic_result, llm_result):
    """Insert or update a record in the llm_reviews table."""
    # Placeholder for real logging
    print("📝 Would log review result for ingredient", ingredient_id)
