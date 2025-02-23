import streamlit as st
import pandas as pd
from query_engine import process_query
from viz import process_visualization
from sqlalchemy import create_engine, inspect
import os
import csv
import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import json
import time

# Custom CSS for better readability
st.markdown(
    """
    <style>
    /* Main title styling */
    h1 {
        color: #1F618D;
        text-align: center;
        font-family: 'Arial', sans-serif;
    }

    /* Header styling */
    h2 {
        color: #154360;
        font-family: 'Arial', sans-serif;
        border-bottom: 2px solid #1F618D;
        padding-bottom: 5px;
    }

    /* Container styling */
    .stContainer {
        background-color: #EAEDED;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }

    /* Button styling */
    .stButton button {
        background-color: #1F618D;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        border: none;
        font-family: 'Arial', sans-serif;
    }

    .stButton button:hover {
        background-color: #154360;
    }

    /* Text input styling */
    .stTextInput input {
        border: 1px solid #1F618D;
        border-radius: 5px;
        padding: 10px;
        font-family: 'Arial', sans-serif;
    }

    /* Dropdown styling */
    .stSelectbox div {
        background-color: #FFFFFF;
        border: 1px solid #1F618D;
        border-radius: 5px;
        padding: 5px;
    }

    .stSelectbox label {
        color: #154360;
        font-family: 'Arial', sans-serif;
    }

    /* Expander styling */
    .stExpander {
        background-color: #FFFFFF;
        border: 1px solid #1F618D;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }

    .stExpander label {
        color: #154360;
        font-family: 'Arial', sans-serif;
    }

    /* Chatbot response styling */
    .chatbot-response {
        background-color: #D5F5E3;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        color: #154360;
        font-family: 'Arial', sans-serif;
    }

    /* User query styling */
    .user-query {
        background-color: #FAD7A0;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        color: #154360;
        font-family: 'Arial', sans-serif;
    }

    /* Conversation history styling */
    .conversation-history {
        background-color: #FFFFFF;
        border: 1px solid #1F618D;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
    }

    /* Timestamp styling */
    .timestamp {
        color: #7F8C8D;
        font-size: 0.9em;
        font-family: 'Arial', sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# App Title
st.title('DataTalk: Natural Language to Data Query')

# Initialize conversation history
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Function to initialize chat log file
def initialize_chat_log():
    if not os.path.exists('chat_log.csv'):
        with open('chat_log.csv', 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['User Query', 'Chatbot Response', 'Timestamp'])

# Initialize chat log file
initialize_chat_log()

# Tabs for Data Query and Conversation History
tab1, tab2 = st.tabs(["Data Query", "Conversation History"])

with tab1:
    # File Upload Section
    with st.container():
        st.header("Upload Your Data")
        uploaded_file = st.file_uploader("Upload your Excel/CSV/SQL file", type=['csv', 'xlsx', 'sql'])

    if uploaded_file:
        file_type = uploaded_file.name.split('.')[-1]

        # Handling Excel and CSV Files
        if file_type in ['csv', 'xlsx']:
            if file_type == 'csv':
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            with st.expander("Data Preview"):
                st.write(df.head())

        # Handling SQL Files
        elif file_type == 'sql':
            # Ensure the 'data' directory exists
            if not os.path.exists('data'):
                os.makedirs('data')

            # Save file to local storage
            file_path = os.path.join('data', uploaded_file.name)
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            
            try:
                engine = create_engine(f'sqlite:///{file_path}')
                inspector = inspect(engine)
                table_names = inspector.get_table_names()
                st.write("Available Tables:", table_names)

                # Selecting Table
                selected_table = st.selectbox("Select Table", table_names)
                query = f"SELECT * FROM {selected_table} LIMIT 5"
                df = pd.read_sql_query(query, engine)
                with st.expander("Data Preview"):
                    st.write(df.head())
            except Exception as e:
                st.error(f"Error reading SQL file: {e}")

        # Add Filters Section
        st.subheader("Filter Data")
        if uploaded_file:
            column_to_filter = st.selectbox("Select a column to filter", df.columns)
            
            if pd.api.types.is_numeric_dtype(df[column_to_filter]):
                min_val = float(df[column_to_filter].min())
                max_val = float(df[column_to_filter].max())
                selected_range = st.slider("Select a range", min_val, max_val, (min_val, max_val))
                filtered_df = df[(df[column_to_filter] >= selected_range[0]) & (df[column_to_filter] <= selected_range[1])]
            else:
                unique_values = df[column_to_filter].unique()
                selected_values = st.multiselect("Select values", unique_values, default=unique_values)
                filtered_df = df[df[column_to_filter].isin(selected_values)]
            
            st.write("Filtered Data:", filtered_df)

        # Natural Language Query Section
        with st.container():
            st.header("Natural Language Query")
            user_query = st.text_input("Ask your question in natural language")

            if user_query:
                # Add a progress bar
                with st.spinner("Processing your query..."):
                    progress_bar = st.progress(0)
                    for i in range(100):
                        time.sleep(0.01)  # Simulate processing time
                        progress_bar.progress(i + 1)
                    
                    result_df = process_query(user_query, df)
                    st.success("Query processed successfully!")

                with st.expander("Query Result"):
                    st.write(result_df)

                # Append to conversation history
                st.session_state.conversation_history.append(("You", user_query))
                
                # Convert result to string based on its type
                if isinstance(result_df, pd.DataFrame):
                    result_str = result_df.to_string()
                elif isinstance(result_df, (int, float)):
                    result_str = str(result_df)
                elif isinstance(result_df, pd.Series):
                    result_str = result_df.to_string()
                elif isinstance(result_df, dict):
                    result_str = json.dumps(result_df, indent=4)
                elif isinstance(result_df, tuple):
                    result_str = str(result_df)
                elif isinstance(result_df, list):
                    result_str = ", ".join(map(str, result_df))
                else:
                    result_str = "⚠️ No valid result found."

                st.session_state.conversation_history.append(("Chatbot", result_str))

                # Save to chat log
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open('chat_log.csv', 'a', newline='', encoding='utf-8') as csvfile:
                    csv_writer = csv.writer(csvfile)
                    csv_writer.writerow([user_query, result_str, timestamp])
        
        # Visualization Query Section
        with st.container():
            st.header("Visualization Query")
            viz_query = st.text_input("Enter your visualization query")
            if viz_query:
                code = process_visualization(viz_query, df)
                with st.expander("Generated Code"):
                    st.code(code)

                # Append to conversation history
                st.session_state.conversation_history.append(("You", viz_query))
                st.session_state.conversation_history.append(("Chatbot", code))

                # Save to chat log
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open('chat_log.csv', 'a', newline='', encoding='utf-8') as csvfile:
                    csv_writer = csv.writer(csvfile)
                    csv_writer.writerow([viz_query, code, timestamp])

                # Execute the generated code
                safe_globals = {"df": df, "pd": pd, "plt": plt, "sns": sns}
                try:
                    exec(code, safe_globals)
                    if 'fig' in safe_globals:
                        st.pyplot(safe_globals['fig'])
                    elif 'result' in safe_globals:
                        st.write(safe_globals['result'])
                    else:
                        st.write("⚠️ No valid result found.")
                except Exception as e:
                    st.error(f"Error executing the generated code: {e}")

with tab2:
    st.header("Conversation History:")
    
    # Display conversation history from session state
    with st.expander("Session History"):
        for speaker, text in st.session_state.conversation_history:
            if speaker == "You":
                st.markdown(f"<div class='user-query'><b>{speaker}:</b> {text}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='chatbot-response'><b>{speaker}:</b> {text}</div>", unsafe_allow_html=True)

    # Display conversation history from chat log file
    if os.path.exists('chat_log.csv'):
        with st.expander("Chat Log History"):
            with open('chat_log.csv', 'r', encoding='utf-8') as csvfile:
                csv_reader = csv.reader(csvfile)
                next(csv_reader, None)  # Skip header
                for row in csv_reader:
                    st.markdown(f"<div class='user-query'><b>User:</b> {row[0]}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='chatbot-response'><b>Chatbot:</b> {row[1]}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='timestamp'>Timestamp: {row[2]}</div>", unsafe_allow_html=True)
                    st.markdown("----")
