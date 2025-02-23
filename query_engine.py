import requests
import pandas as pd
import json

GROQ_API_KEY = "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"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"


# def process_query(user_query, df):
#     columns = df.columns.tolist()
#     column_string = ', '.join(columns)

#     # Constructing Prompt for GROQ
#     prompt = (f"Convert this natural language query into a pandas query: '{user_query}'. "
#               f"The available columns are: {column_string}. "
#               "Be robust and predict column names if they are not exactly mentioned.")

#     # Querying GROQ API
#     headers = {
#         "Authorization": f"Bearer {GROQ_API_KEY}",
#         "Content-Type": "application/json"
#     }
#     data = {
#         "model": "text-davinci-003",
#         "prompt": prompt,
#         "max_tokens": 100,
#         "temperature": 0.2
#     }

#     response = requests.post(GROQ_ENDPOINT, headers=headers, json=data)
#     response_data = response.json()

#     # Extracting Query
#     code_query = response_data['choices'][0]['text'].strip()

#     # Executing the Generated Query
#     try:
#         result_df = eval(code_query)
#         return result_df
#     except Exception as e:
#         return f"Error in query execution: {e}"
    
import requests
import pandas as pd
import json

GROQ_API_KEY = "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"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

def process_query(user_query, df):
    columns = df.columns.tolist()
    column_string = ', '.join(columns)

    # Constructing Prompt for GROQ
    prompt = f"""
    Convert this natural language query into a Pandas command:
    Query: {user_query}

    Dataset structure:
    {df.head(3).to_dict()}

    **Rules:**
    - Use Pandas syntax.
    - Assign the result to `result`.
    - If counting rows, use `.shape[0]`.
    - For min/max values, return both as a tuple `(min, max)`.
    - For percentages, return as a float calculation `(count / total) * 100`.
    - For mode (most common value), return `.mode().tolist()` to handle multiple values.
    - If the query involves grouping and sorting, use `.groupby().sum().sort_values()`.
    - Ensure the output is a single value, a tuple, or a DataFrame, as required by the query.
    - Do **not** redefine `df` or import Pandas.
    - Return only the Pandas command, no explanations.
    - Use Pandas syntax for data manipulation.
    - Assign the result to `result` for data manipulation or `fig` for visualizations.
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
            {"role": "system", "content": "You are an AI that converts natural language queries into Pandas filtering code."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 100,
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

            # Executing the Generated Query
            safe_globals = {"df": df, "pd": pd}
            try:
                exec(code, safe_globals)
                result = safe_globals.get("result", None)
                
                if isinstance(result, pd.DataFrame):
                    return result  # Return filtered DataFrame
                elif isinstance(result, (int, float)):
                    return result  # Return numerical values (min, max, avg)
                elif isinstance(result, pd.Series):
                    return result.to_string()  # Convert Series to string for clean output
                elif isinstance(result, dict):
                    return json.dumps(result, indent=4)  # Pretty-print dictionary (grouped results)
                elif isinstance(result, tuple):
                    return result  # Return tuple (min, max)
                elif isinstance(result, list):
                    return ", ".join(map(str, result))  # Print mode values properly
                else:
                    return "⚠️ No valid result found."
            except Exception as e:
                return f"⚠️ Error in query execution: {e}"
        else:
            return f"⚠️ Unexpected response format: {response_data}"
    else:
        return f"⚠️ API request failed with status code {response.status_code}: {response.text}"
