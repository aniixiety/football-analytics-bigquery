from google.cloud import bigquery
from google import genai
import time
from dotenv import load_dotenv
import os

load_dotenv(".env.football")

bq_client = bigquery.Client(project="football-analytics-507017")
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

conversation_history = []

def call_gemini_with_retry(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = gemini_client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
            )
            return response.text
        except Exception as e:
            if "RESOURCE_EXHAUSTED" in str(e) and attempt < max_retries - 1:
                print("Hit a rate limit, waiting 30 seconds before trying again...")
                time.sleep(30)
            else:
                raise e

def get_schema_text():
    dataset_ref = bq_client.dataset("football_data")
    tables = bq_client.list_tables(dataset_ref)

    schema_text = ""
    for table in tables:
        table_ref = dataset_ref.table(table.table_id)
        table_obj = bq_client.get_table(table_ref)

        schema_text += f"\nTable: `football-analytics-507017.football_data.{table.table_id}`\n"
        for field in table_obj.schema:
            schema_text += f"  - {field.name} ({field.field_type})\n"

    return schema_text


def ask_question(question, schema_text, conversation_history):
    history_text = ""
    for past_question, past_sql in conversation_history[-3:]:
        history_text += f'Previous question: "{past_question}"\nSQL used: {past_sql}\n\n'

    prompt = f"""
You are a BigQuery SQL expert. Here is the database schema:

{schema_text}

Here is the recent conversation history, in case the current question refers back to it:

{history_text}

Write a single BigQuery SQL query that answers this new question:
"{question}"

Rules:
- If the new question refers to something from the conversation history (like "that list" or "only strikers"), use the previous SQL as a starting point and adjust it.
- Only output the raw SQL query, nothing else. No explanation, no markdown formatting, no backticks around the whole answer.
- Table names must always be written exactly as shown above, including the full path and backticks.
- Only write SELECT queries. Never write INSERT, UPDATE, DELETE, or DROP.
"""
    return call_gemini_with_retry(prompt)


def is_safe_query(sql_query):
    forbidden_words = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "MERGE"]
    upper_query = sql_query.upper()

    for word in forbidden_words:
        if word in upper_query:
            return False

    return True


def run_query(sql_query):
    query_job = bq_client.query(sql_query)
    results = query_job.result()

    rows = [dict(row) for row in results]
    return rows


def answer_in_plain_english(question, rows):
    prompt = f"""
The user asked: "{question}"

Here is the raw query result:
{rows}

Answer the user's question in one or two plain, friendly sentences using this data.
Do not mention SQL, queries, or databases. Just answer like a knowledgeable person would.
"""

    return call_gemini_with_retry(prompt)


if __name__ == "__main__":
    schema_text = get_schema_text()

    print("Football Analytics Chatbot")
    print("Type your question, or type 'quit' to stop.\n")

    while True:
        question = input("Ask something: ")

        if question.lower() == "quit":
            break

        sql_query = ask_question(question, schema_text, conversation_history)

        print("\nGenerated SQL:")
        print(sql_query)

        if is_safe_query(sql_query):
            try:
                rows = run_query(sql_query)
                final_answer = answer_in_plain_english(question, rows)
                print("\nAnswer:")
                print(final_answer)

                conversation_history.append((question, sql_query))
            except Exception as e:
                print("\nSomething went wrong running that query:")
                print(e)
        else:
            print("Blocked: this query was not a safe read-only query.")

        print("\n" + "-" * 40 + "\n")