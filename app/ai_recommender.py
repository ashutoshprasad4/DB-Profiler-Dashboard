# app/ai_recommender.py
import os
import json
import google.generativeai as genai

# Configure the generative AI model
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    # --- FIX: Updated the model name to a current, recommended version ---
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"⚠️ Error configuring Generative AI: {e}. The AI recommender will be disabled.")
    model = None

def get_llm_recommendation_for_query(query_data: dict) -> dict:
    """
    Uses a generative AI model to analyze a single slow query and provide recommendations.
    """
    if not model:
        return {"reason": "AI model is not configured. Please check your API key."}
        
    # Construct a detailed prompt for the AI model
    prompt = f"""
    You are an expert PostgreSQL Database Administrator (DBA). Your task is to analyze the following slow query and provide a detailed, actionable recommendation.

    **Query Analysis Data:**
    - **SQL Query:** `{query_data.get('query', 'N/A')}`
    - **Execution Time (ms):** `{query_data.get('execution_time', 'N/A')}`
    - **Rows Examined:** `{query_data.get('rows_examined', 'N/A')}`
    - **Initial Heuristic Findings:** `{query_data.get('reasons', [])}`

    **Instructions:**
    Respond with a single, minified JSON object containing one key: "reason".
    The value should be a detailed, human-readable string (using Markdown for formatting like bolding or lists) that:
    1.  Explains in plain English why this query is likely slow, based on the provided data.
    2.  Provides a concrete, actionable recommendation for how to improve it (e.g., suggest a specific index to create, or show a rewritten version of the query).
    
    **Example JSON Output:**
    {{"reason": "The query is slow because it's performing a full table scan on a large number of rows. \\n\\n**Recommendation:** Create an index on the `users` table to speed up lookups. You can do this with the following command: \\n`CREATE INDEX idx_users_email ON users(email);`"}}
    """

    try:
        response = model.generate_content(prompt)
        if not response.text:
            return {"reason": "AI model returned an empty response, possibly due to content safety filters."}

        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        result = json.loads(cleaned_response)
        return result
    except Exception as e:
        return {"reason": f"AI analysis failed due to an error: {e}."}

