import sqlite3
import time
import pandas as pd
import streamlit as st
from groq import Groq

client = Groq(api_key=st.secrets['GROQ_API_KEY'])

# mode=ro opens the database read-only, so nothing can be changed even if a bad query gets through
conn = sqlite3.connect('file:chinook.db?mode=ro', uri=True)
cursor = conn.cursor()

cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
schema = "\n\n".join([row[0] for row in cursor.fetchall()])


def get_sql(question):
    prompt = f"""
You are an expert SQL assistant.
Given the following database schema, write a valid SQLite query to answer the user's question.
Return ONLY the raw SQL query. Do not include markdown formatting, backticks, or explanations.

Schema:
{schema}

Rules:
- Write ONLY read-only SELECT queries.
- Never write DROP, DELETE, UPDATE, INSERT, or ALTER statements.
- Round money to 2 decimals.

Question: {question}
SQL Query:
"""
    response = client.chat.completions.create(
        model='openai/gpt-oss-120b',
        messages=[{'role': 'user', 'content': prompt}],
    )
    sql = response.choices[0].message.content.strip()
    sql = sql.replace('```sql', '').replace('```', '').strip()
    return sql


def is_query_safe(sql):
    forbidden_words = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'ATTACH', 'PRAGMA']
    cleaned_query = sql.strip().upper()

    if not (cleaned_query.startswith('SELECT') or cleaned_query.startswith('WITH')):
        return False, 'Only SELECT queries are allowed.'

    # swap ; and ( for spaces so things like "...;DROP TABLE" still get split into separate words
    words = cleaned_query.replace(';', ' ').replace('(', ' ').split()
    for word in forbidden_words:
        if word in words:
            return False, f"Blocked: found '{word}' in the query."

    return True, 'Safe'


st.title('Natural Language Database Copilot')
st.write('Ask a question about the Chinook music store database in plain English. '
         'The app writes the SQL, checks that it only reads data, and runs it.')

st.sidebar.header('Example questions')
st.sidebar.write('- Who are the top 5 customers by total spending?')
st.sidebar.write('- What are the top 10 best selling genres?')
st.sidebar.write('- How much revenue did we make each year?')
st.sidebar.write('- Which sales rep brought in the most revenue?')
st.sidebar.write('- Which artists have the most albums?')

question = st.text_input('Ask a question about the database:')

if st.button('Search') and question:
    sql = get_sql(question)
    st.subheader('Generated SQL')
    st.code(sql, language='sql')

    is_safe, message = is_query_safe(sql)
    if not is_safe:
        st.error(message)
    else:
        try:
            start = time.time()
            results = pd.read_sql_query(sql, conn)
            seconds = time.time() - start

            st.subheader('Results')
            st.dataframe(results)
            st.caption(f'{len(results)} rows, ran in {seconds:.3f} seconds')
        except Exception as e:
            st.error(f"The query didn't work: {e}")
