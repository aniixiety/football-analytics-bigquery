import streamlit as st
from ask_football import get_schema_text, ask_question, is_safe_query, run_query, answer_in_plain_english

st.set_page_config(page_title="Football Analytics Chatbot")

st.title("Football Analytics Chatbot")
st.write("Ask a question about the football database in plain English.")

if "schema_text" not in st.session_state:
    st.session_state.schema_text = get_schema_text()

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

question = st.chat_input("Ask something about the data...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            sql_query = ask_question(
                question,
                st.session_state.schema_text,
                st.session_state.conversation_history
            )

            if is_safe_query(sql_query):
                try:
                    rows = run_query(sql_query)
                    final_answer = answer_in_plain_english(question, rows)

                    st.session_state.conversation_history.append((question, sql_query))

                    st.write(final_answer)

                    with st.expander("Show the SQL that was used"):
                        st.code(sql_query, language="sql")

                except Exception as e:
                    final_answer = f"Something went wrong running that query: {e}"
                    st.write(final_answer)
            else:
                final_answer = "That question would have required a query I'm not allowed to run, so I blocked it."
                st.write(final_answer)

    st.session_state.messages.append({"role": "assistant", "content": final_answer})