import os
import json
import pandas as pd
import google.generativeai as genai

# Configure the generative AI model
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"⚠️ Error configuring Generative AI: {e}. The chatbot will be disabled.")
    model = None

def get_chatbot_response(chat_history: list, question: str, context_data: str) -> str:
    """
    Uses a generative AI model to have a conversation about query performance.
    """
    if not model:
        return "The AI chatbot is not configured. Please check the API key."
        
    # Construct a detailed prompt for the AI model
    prompt = f"""
    You are an expert PostgreSQL Database Administrator (DBA) acting as an interactive chatbot assistant. 
    Your goal is to help a developer understand and optimize their database queries.

    This is the conversation history so far:
    {json.dumps(chat_history)}

    This is the data context for the user's question (a JSON representation of relevant query logs):
    {context_data}

    This is the user's new question:
    "{question}"

    Instructions:
    - Analyze the user's question in the context of the conversation history and the provided data.
    - Provide a concise, clear, and helpful answer.
    - If you give a recommendation, make it actionable (e.g., suggest a specific index).
    - Refer to queries by their query_id (e.g., Q6, Q10).
    - Use Markdown for formatting if it improves readability.
    """

    try:
        response = model.generate_content(prompt)
        if not response.text:
            return "The AI model returned an empty response, possibly due to content safety filters."
        
        return response.text
    except Exception as e:
        return f"An error occurred while communicating with the AI model: {e}"