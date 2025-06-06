import streamlit as st
import pandas as pd
from action_center import show_action_center_top10
from ai_qna import show_ai_qna
from ai_insights import show_revenue_drop_insight, show_ivt_margin_alert, show_revenue_drop_table

st.set_page_config(page_title="AI Revenue Action Center", layout="wide")
st.title("📈 AI-Powered Revenue Action Center")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

def safe_col(df, name):
    """Find column in df matching name (case/space insensitive)."""
    for c in df.columns:
        if c.strip().lower() == name.strip().lower():
            return c
    return None

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write("Columns detected:", df.columns.tolist())  # Remove this after debugging

    # Safely find column names
    advertiser_col = safe_col(df, 'Advertiser')
    channel_col = safe_col(df, 'Channel')
    adformat_col = safe_col(df, 'Ad format')

    advertisers = ["(All)"]
    if advertiser_col:
        advertisers += sorted([str(x) for x in df[advertiser_col].dropna().unique()])
    channels = ["(All)"]
    if channel_col:
        channels += sorted([str(x) for x in df[channel_col].dropna().unique()])
    formats = ["(All)"]
    if adformat_col:
        formats += sorted([str(x) for x in df[adformat_col].dropna().unique()])

    col1, col2, col3 = st.columns(3)
    with col1:
        advertiser = st.selectbox("Advertiser", options=advertisers, index=0)
    with col2:
        channel = st.selectbox("Channel", options=channels, index=0)
    with col3:
        ad_format = st.selectbox("Ad Format", options=formats, index=0)

    filtered = df.copy()
    if advertiser != "(All)" and advertiser_col:
        filtered = filtered[filtered[advertiser_col] == advertiser]
    if channel != "(All)" and channel_col:
        filtered = filtered[filtered[channel_col] == channel]
    if ad_format != "(All)" and adformat_col:
        filtered = filtered[filtered[adformat_col] == ad_format]

    # ---- Revenue Drop Insight Card ----
    if advertiser != "(All)" and advertiser_col:
        st.markdown(f"### 📉 Why Did Revenue Drop for **{advertiser}**?")
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
