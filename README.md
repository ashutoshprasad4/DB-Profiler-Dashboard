# DB Profiler

## Setup

1.  **Create and activate virtualenv**
    ```bash
    python -m venv .venv
    .venv\Scripts\activate  # On Windows
    # source .venv/bin/activate  # On macOS/Linux
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    
3.  **Configure API Key**
    Create a `.env` file in the project root with your Google API Key.
    ```
    GOOGLE_API_KEY='YOUR_SECRET_API_KEY_HERE'
    ```

    * **How to Get an API Key**: A Google API Key is required for the AI assistant.
        1.  Go to **[Google AI Studio](https://aistudio.google.com/app/apikey)**.
        2.  Sign in and click **"Create API key"**.
        3.  Copy the generated key and paste it into your `.env` file. Treat this key like a password.

    * **AI Model Used**: This project uses the `gemini-1.5-flash` model via the `google-generativeai` library.

4.  **Generate synthetic logs (Optional)**
    ```bash
    python app/generator.py
    ```

5.  **Run the API Server**
    In your first terminal, run:
    ```bash
    uvicorn app.api:app --reload --port 8000
    ```

6.  **Run the Dashboard**
    In a second terminal, run:
    ```bash
    streamlit run app/dashboard.py
    ```

## API Usage Examples (via cURL)

* **Analyze logs (POST /analyze)**
    ```bash
    curl -X POST "http://localhost:8000/analyze" -H "Content-Type: application/json" -d "{\"csv_path\":\"examples/sample_logs.csv\"}"
    ```
* **Get AI recommendation (POST /get-llm-recommendation)**
    ```bash
    curl -X POST "http://localhost:8000/get-llm-recommendation" -H "Content-Type: application/json" -d "{\"query\":\"SELECT * FROM users WHERE id = 123\",\"execution_time\":500.0,\"rows_examined\":10000,\"reasons\":[\"Large rows examined\"]}"
    ```

## Postgres simulation
Set environment variables `PG_HOST`, `PG_PORT`, `PG_DB`, `PG_USER`, `PG_PASS` to point to a sandbox DB. The simulator functionality is present in `app/simulator.py` but is not yet integrated into the main dashboard workflow.

## Next steps / improvements
-   Integrate the Postgres simulator into the dashboard to test AI recommendations.
-   Add a caching layer to store and retrieve AI recommendations to reduce API calls.
-   Implement a learned cost model (train regressor on observed exec_time / plan features).
-   Add a non-blocking simulator (e.g., run in an ephemeral Docker DB) for safe testing.