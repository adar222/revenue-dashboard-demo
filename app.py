import streamlit as st
import pandas as pd
from action_center import show_action_center_top10, show_dropped_channels, show_best_worst_formats
from ai_qna import show_ai_qna

st.set_page_config(page_title="AI Revenue Action Center", layout="wide")

st.title("📈 AI-Powered Revenue Action Center")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # --- Filtering ---
    advertisers = df['Advertiser'].dropna().unique()
    channels = df['Channel'].dropna().unique()
    formats = df['Ad format'].dropna().unique()
    
    default_adv = advertisers[0] if len(advertisers) else None
    default_chn = channels[0] if len(channels) else None
    default_fmt = formats[0] if len(formats) else None

    col1, col2, col3 = st.columns(3)
    with col1:
        advertiser = st.selectbox("Advertiser", options=advertisers, index=0 if default_adv in advertisers else 0)
    with col2:
        channel = st.selectbox("Channel", options=channels, index=0 if default_chn in channels else 0)
    with col3:
        ad_format = st.selectbox("Ad Format", options=formats, index=0 if default_fmt in formats else 0)

    # Filtered data
    filtered = df[
        (df['Advertiser'] == advertiser) &
        (df['Channel'] == channel) &
        (df['Ad format'] == ad_format)
    ].copy()
    
    st.markdown("---")

    # --- Insights & Actions ---
    show_dropped_channels(filtered)
    show_best_worst_formats(filtered)
    show_action_center_top10(filtered)

    st.markdown("---")

    # --- AI Q&A Section ---
    st.markdown("## 💬 Ask AI About Your Data (Optional)")
    api_key = st.text_input("Paste your OpenAI API key to enable AI analysis (will not be saved):", type="password")
    if api_key:
        show_ai_qna(filtered, api_key)
    else:
        st.info("Enter your OpenAI API key above to enable AI Q&A.")
else:
    st.info("Please upload your Excel file to see all action items and enable filtering.")
