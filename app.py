import streamlit as st
import pandas as pd
from action_center import show_action_center_top10, show_dropped_channels, show_best_worst_formats
from ai_qna import show_ai_qna
from ai_insights import show_ai_insights

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
        st.stop()
    # ---- SANITY CHECK END ----

    tab1, tab2 = st.tabs(["Dashboard", "AI Insights"])

    with tab1:
        st.markdown("#### 🚦 Executive Summary")

        ai_cols = [
            'Date', 'Advertiser', 'Channel', 'Ad format', 'Package', 'Gross Revenue', 'eCPM', 'FillRate',
            'Publisher Impressions', 'IVT (%)', 'Margin (%)', 'Score', 'Alert', 'Status'
        ]
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

        # --- KPIs (formatted)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Rows", f"{len(filtered):,}")
        if "Status" in filtered.columns:
            c2.metric("Critical", f"{(filtered['Status'] == 'Critical').sum():,}")
            c3.metric("Needs Review", f"{(filtered['Status'] == 'Needs Review').sum():,}")
        if "IVT (%)" in filtered.columns:
            ivt = int(round(filtered["IVT (%)"].mean()))
            c4.metric("Avg IVT (%)", f"{ivt}%")
        if "Margin (%)" in filtered.columns:
            margin = int(round(filtered["Margin (%)"].mean()))
            c5.metric("Avg Margin (%)", f"{margin}%")

        st.divider()

        # --- Top 5 Risky Packages (formatted)
        st.markdown("##### 🚨 Top 5 Risky Packages")
        if "Status" in filtered.columns:
            risky = filtered[filtered['Status'].isin(['Critical', 'Needs Review'])].copy()
            if not risky.empty:
                risky = risky.sort_values(
                    by=["Status", "Score", "Gross Revenue"], 
                    ascending=[True, True, False]
                ).head(5)
                show_cols = [c for c in ['Package', 'Gross Revenue', 'IVT (%)', 'Margin (%)', 'Score', 'Status', 'Alert'] if c in risky.columns]
                display = risky[show_cols].copy()

                if 'Gross Revenue' in display.columns:
                    display['Gross Revenue'] = display['Gross Revenue'].apply(lambda x: f"{x:,.0f}")
                if 'IVT (%)' in display.columns:
                    display['IVT (%)'] = display['IVT (%)'].apply(lambda x: f"{int(round(x))}%")
                if 'Margin (%)' in display.columns:
                    display['Margin (%)'] = display['Margin (%)'].apply(lambda x: f"{int(round(x))}%")
                if 'Score' in display.columns:
                    display['Score'] = display['Score'].apply(lambda x: f"{int(x)}")

                st.dataframe(display, use_container_width=True, height=250)
            else:
                st.info("No risky packages found for this selection.")

        st.divider()

        # --- AI Highlights (executive-style summary)
        st.markdown("##### 🤖 AI Highlights")
        highlights = []
        if "IVT (%)" in filtered.columns:
            worst_ivt = filtered.sort_values("IVT (%)", ascending=False).head(1)
            if not worst_ivt.empty:
                highlights.append(f"Highest IVT: **{worst_ivt['Package'].values[0]}** at **{int(round(worst_ivt['IVT (%)'].values[0]))}%**")
        if "Margin (%)" in filtered.columns:
            worst_margin = filtered.sort_values("Margin (%)", ascending=True).head(1)
            if not worst_margin.empty:
                highlights.append(f"Lowest Margin: **{worst_margin['Package'].values[0]}** at **{int(round(worst_margin['Margin (%)'].values[0]))}%**")
        if "Gross Revenue" in filtered.columns:
            top_rev = filtered.sort_values("Gross Revenue", ascending=False).head(1)
            if not top_rev.empty:
                highlights.append(f"Top Revenue: **{top_rev['Package'].values[0]}** with **${int(round(top_rev['Gross Revenue'].values[0])):,}**")
        for h in highlights:
            st.write(f"- {h}")

        st.divider()

        # Optional: "Show all data table" button
        if st.button("Show all data table"):
            formatted = filtered[ai_cols].copy()
            if 'IVT (%)' in formatted.columns:
                formatted['IVT (%)'] = formatted['IVT (%)'].apply(lambda x: f"{int(round(x))}%")
            if 'Margin (%)' in formatted.columns:
                formatted['Margin (%)'] = formatted['Margin (%)'].apply(lambda x: f"{int(round(x))}%")
            if 'eCPM' in formatted.columns:
                formatted['eCPM'] = formatted['eCPM'].apply(lambda x: f"{x:,.2f}")
            if 'FillRate' in formatted.columns:
                formatted['FillRate'] = formatted['FillRate'].apply(lambda x: f"{int(round(x*100))}%")
            for col in ['Gross Revenue', 'Publisher Impressions']:
                if col in formatted.columns:
                    formatted[col] = formatted[col].apply(lambda x: f"{x:,.0f}")
            st.dataframe(formatted, use_container_width=True, height=500)

        # --- You can keep or remove these lines if you want action_center sections too ---
        # show_dropped_channels(filtered)
        # show_best_worst_formats(filtered)
        # show_action_center_top10(filtered)

        st.markdown("---")
        st.markdown("## 💬 Ask AI About Your Data (Optional)")
        api_key = st.text_input("Paste your OpenAI API key to enable AI analysis (will not be saved):", type="password")
        if api_key:
            show_ai_qna(filtered, api_key)
        else:
            st.info("Enter your OpenAI API key above to enable AI Q&A.")

    with tab2:
        show_ai_insights(df)

else:
    st.info("Please upload your Excel file to see all action items and enable filtering.")
