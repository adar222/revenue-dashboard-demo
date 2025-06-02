import streamlit as st
import openai
import pandas as pd

def show_ai_qna(df, api_key):
    st.markdown("### 🤖 Ask AI About Your Data")
    question = st.text_area(
        "Ask a question about the data (e.g., 'Which channel should I prioritize?', 'Why did revenue drop for X?')", 
        height=70
    )

    if st.button("Ask AI"):
        with st.spinner("AI is thinking..."):
            try:
                # Use OpenAI 1.x style
                client = openai.OpenAI(api_key=api_key)
                # Convert first 500 rows to CSV for AI context
                sample = df.head(500).to_csv(index=False)
                prompt = (
                    "You are a professional programmatic analyst AI. "
                    "Here is a sample of my data (CSV columns: " +
                    ", ".join(df.columns) +
                    ").\n\n"
                    "DATA SAMPLE (first 500 rows):\n"
                    f"{sample}\n\n"
                    f"USER QUESTION: {question}\n\n"
                    "Answer as a business analyst, giving clear action steps or explanations."
                )
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=512,
                    temperature=0.2
                )
                answer = response.choices[0].message.content
                st.success(answer)
            except Exception as e:
                st.error(f"AI error: {e}")
