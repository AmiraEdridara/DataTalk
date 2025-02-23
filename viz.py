import requests
import pandas as pd
import json

GROQ_API_KEY = "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"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

def process_visualization(user_query, df):
    columns = df.columns.tolist()
    column_string = ', '.join(columns)

    # Constructing Prompt for GROQ
    prompt = f"""
    Convert this natural language query into a visualization code using matplotlib or seaborn:
    Query: {user_query}

    Dataset structure:
    {df.head(3).to_dict()}

    **Rules:**
    - Use matplotlib or seaborn for visualizations.
    - Assign the result to `fig` for visualizations.
    - Do **not** redefine `df` or import Pandas.
    - Return only the code, no explanations.
    """

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are an AI that converts natural language queries into visualization code using matplotlib or seaborn."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 150,
        "temperature": 0.2
    }

    response = requests.post(GROQ_ENDPOINT, headers=headers, data=json.dumps(payload))

    # Check for successful response
    if response.status_code == 200:
        response_data = response.json()
        print("Response Data:", response_data)  # Debugging Line
        
        # Safely check for 'choices' key
        if 'choices' in response_data:
            code = response_data["choices"][0]["message"]["content"].strip()
            code = code.replace("```python", "").replace("```", "").strip()

            # Prevent code from redefining the dataset
            if "pd.DataFrame" in code or "import pandas" in code or "df =" in code:
                return "⚠️ Invalid code generated. Skipping execution."

            return code
        else:
            return f"⚠️ Unexpected response format: {response_data}"
    else:
        return f"⚠️ API request failed with status code {response.status_code}: {response.text}"
