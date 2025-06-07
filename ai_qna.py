import streamlit as st
import openai

def show_ai_qna(df, api_key):
    st.markdown("#### 🤖 Ask AI About Your Data")
    question = st.text_input("Ask a question about the filtered data below (English only):")
    if st.button("Ask"):
        # Summarize the filtered table for GPT context (truncated for token limit)
        csv_text = df.head(25).to_csv(index=False)
        prompt = (
            "You are a business analyst. Here is sample data:\n"
            + csv_text +
            f"\nQuestion: {question}\n"
            "Give your answer in 2-4 sentences. Be specific and use numbers from the table if possible."
        )
        try:
            openai.api_key = api_key
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role":"user","content": prompt}],
                temperature=0.3
            )
            st.markdown("**AI Answer:**")
            st.success(resp['choices'][0]['message']['content'])
        except Exception as e:
            st.error(f"AI request failed: {e}")
