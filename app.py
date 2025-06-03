import streamlit as st
import pandas as pd
from action_center import show_action_center_top10, show_dropped_channels, show_best_worst_formats
from ai_qna import show_ai_qna
from ai_insights import show_ai_insights  # Make sure this is imported!

st.set_page_config(page_title="AI Revenue Action Center", layout="wide")
st.title("📈 AI-Powered Revenue Action Center")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # ---- SANITY CHECK START ----
    required_columns = [
        'Date', 'Package', 'Gross Revenue', 'eCPM', 'FillRate',
        'Publisher Impressions', 'Ad format'
    ]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        st.error(f"ERROR: The following required columns are missing from your Excel: {', '.join(missing)}")
        st.stop()  # Don't continue if critical columns are missing
    # ---- SANITY CHECK END ----

    # --- NEW: Tabs layout ---
    tab1, tab2 = st.tabs(["Dashboard", "AI Insights"])

    # ---- Dashboard tab ----
    with tab1:
        st.markdown("#### 📊 Main Data Table (AI-Enhanced)")

        # --- 1. Show all relevant columns ---
        ai_cols = [
            'Date', 'Advertiser', 'Channel', 'Ad format', 'Package', 'Gross Revenue', 'eCPM', 'FillRate',
            'Publisher Impressions', 'IVT (%)', 'Margin (%)', 'Score', 'Alert', 'Status'
        ]
        # Only show columns that exist in the current dataframe
        ai_cols = [col for col in ai_cols if col in df.columns]

        advertisers = df['Advertiser'].dropna().unique().tolist() if 'Advertiser' in df.columns else []
        channels = df['Channel'].dropna().unique().tolist() if 'Channel' in df.columns else []
        formats = df['Ad format'].dropna().unique().tolist()

        advertisers = ["(All)"] + advertisers if advertisers else ["(All)"]
        channels = ["(All)"] + channels if channels else ["(All)"]
        formats = ["(All)"] + formats

        col1, col2, col3 = st.columns(3)
        with col1:
            advertiser = st.selectbox("Advertiser", options=advertisers, index=0)
        with col2:
            channel = st.selectbox("Channel", options=channels, index=0)
        with col3:
            ad_format = st.selectbox("Ad Format", options=formats, index=0)

        filtered = df.copy()
        if advertiser != "(All)" and 'Advertiser' in df.columns:
            filtered = filtered[filtered['Advertiser'] == advertiser]
        if channel != "(All)" and 'Channel' in df.columns:
            filtered = filtered[filtered['Channel'] == channel]
        if ad_format != "(All)":
            filtered = filtered[filtered['Ad format'] == ad_format]

        # --- 2. Quick summary stats ---
        st.markdown("##### Summary Stats")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Rows", len(filtered))
        if "Status" in filtered.columns:
            c2.metric("Critical", (filtered["Status"] == "Critical").sum())
            c3.metric("Needs Review", (filtered["Status"] == "Needs Review").sum())
        if "IVT (%)" in filtered.columns:
            c4.metric("Avg IVT (%)", round(filtered["IVT (%)"].mean(), 2))
        if "Margin (%)" in filtered.columns:
            c5.metric("Avg Margin (%)", round(filtered["Margin (%)"].mean(), 2))

        st.divider()

        # --- 3. Highlight rows: red for "Critical", yellow for "Needs Review" ---
        def highlight_risk(row):
            if "Status" in row:
                if row["Status"] == "Critical":
                    return ['background-color: #ffcccc'] * len(row)
                elif row["Status"] == "Needs Review":
                    return ['background-color: #fff3cd'] * len(row)
            return [''] * len(row)

        st.markdown("##### All Packages (scroll right ➡️ to see all AI columns)")
        st.dataframe(filtered[ai_cols].style.apply(highlight_risk, axis=1), use_container_width=True, height=520)

        st.divider()

        # --- 4. Show ONLY the risky packages in a separate table ---
        if "Status" in filtered.columns:
            risky = filtered[filtered['Status'].isin(['Critical', 'Needs Review'])]
            st.markdown("##### 🚨 Risky Packages (Critical & Needs Review)")
            if not risky.empty:
                st.dataframe(risky[ai_cols].style.apply(highlight_risk, axis=1), use_container_width=True, height=320)
            else:
                st.info("No risky packages found for this selection.")

        st.markdown("---")
        show_dropped_channels(filtered)
        show_best_worst_formats(filtered)
        show_action_center_top10(filtered)
        st.markdown("---")
        st.markdown("## 💬 Ask AI About Your Data (Optional)")
        api_key = st.text_input("Paste your OpenAI API key to enable AI analysis (will not be saved):", type="password")
        if api_key:
            show_ai_qna(filtered, api_key)
        else:
            st.info("Enter your OpenAI API key above to enable AI Q&A.")

    # ---- AI Insights tab ----
    with tab2:
        show_ai_insights(df)

else:
    st.info("Please upload your Excel file to see all action items and enable filtering.")
