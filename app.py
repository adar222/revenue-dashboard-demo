import streamlit as st
import pandas as pd
from action_center import show_action_center_top10
from ai_qna import show_ai_qna
from ai_insights import show_revenue_drop_insight, show_ivt_margin_alert, show_revenue_drop_table

st.set_page_config(page_title="AI Revenue Action Center", layout="wide")
st.title("📈 AI-Powered Revenue Action Center")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Filters
    advertisers = ["(All)"] + sorted(df['Advertiser'].dropna().unique().tolist())
    channels = ["(All)"] + sorted(df['Channel'].dropna().unique().tolist())
    formats = ["(All)"] + sorted(df['Ad format'].dropna().unique().tolist())

    col1, col2, col3 = st.columns(3)
    with col1:
        advertiser = st.selectbox("Advertiser", options=advertisers, index=0)
    with col2:
        channel = st.selectbox("Channel", options=channels, index=0)
    with col3:
        ad_format = st.selectbox("Ad Format", options=formats, index=0)

    filtered = df.copy()
    if advertiser != "(All)":
        filtered = filtered[filtered['Advertiser'] == advertiser]
    if channel != "(All)":
        filtered = filtered[filtered['Channel'] == channel]
    if ad_format != "(All)":
        filtered = filtered[filtered['Ad format'] == ad_format]

    # ---- Revenue Drop Insight Card ----
    if advertiser != "(All)":
        st.markdown("### 📉 Why Did Revenue Drop for **{}**?".format(advertiser))
        show_revenue_drop_insight(df, advertiser)
        st.markdown("---")

    # ---- Action Center: Top 10 Trending Packages ----
    st.markdown("### 🚀 Action Center: Top 10 Trending Packages (3d vs Prev 3d)")
    show_action_center_top10(filtered)
    st.markdown("---")

    # ---- IVT & Margin Alert (Last Day) ----
    st.markdown("### 🛡️ IVT & Margin Alert (Last Day)")
    show_ivt_margin_alert(filtered)
    st.markdown("---")

    # ---- Revenue Drop Table (Last Day, Rev > $50, Drop >20%) ----
    st.markdown("### 📉 Revenue Drop Alert (Rev > $50, >20%)")
    show_revenue_drop_table(filtered)
    st.markdown("---")

    # ---- AI Chatbot ----
    st.markdown("### 🤖 Ask AI About Your Data (Optional)")
    api_key = st.text_input("Paste your OpenAI API key to enable AI analysis (will not be saved):", type="password")
    if api_key:
        show_ai_qna(filtered, api_key)
    else:
        st.info("Enter your OpenAI API key above to enable AI Q&A.")

else:
    st.info("Please upload your Excel file to see all action items and enable filtering.")
