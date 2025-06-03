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
    st.markdown("#### 🚦 Executive Summary")

    ai_cols = [
        'Date', 'Advertiser', 'Channel', 'Ad format', 'Package', 'Gross Revenue', 'eCPM', 'FillRate',
        'Publisher Impressions', 'IVT (%)', 'Margin (%)', 'Score', 'Alert', 'Status'
    ]
    ai_cols = [col for col in ai_cols if col in df.columns]

    # KPIs (formatted)
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

    # Top 5 Risky Packages (sorted by Score, then revenue), formatted
    st.markdown("##### 🚨 Top 5 Risky Packages")
    if "Status" in filtered.columns:
        risky = filtered[filtered['Status'].isin(['Critical', 'Needs Review'])].copy()
        if not risky.empty:
            # Sort: Critical first, then Needs Review, by Score ASC (riskier) then revenue DESC
            risky = risky.sort_values(
                by=["Status", "Score", "Gross Revenue"], 
                ascending=[True, True, False]
            ).head(5)
            show_cols = [c for c in ['Package', 'Gross Revenue', 'IVT (%)', 'Margin (%)', 'Score', 'Status', 'Alert'] if c in risky.columns]
            display = risky[show_cols].copy()

            # Format columns
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

    # AI Highlights - Demo version with text, you can later use AI logic!
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

    # Optional: "Show all data" button
    if st.button("Show all data table"):
        # Format main table: IVT, Margin as int %; eCPM and FillRate as requested; commas for big numbers
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


    # ---- AI Insights tab ----
    with tab2:
        show_ai_insights(df)

else:
    st.info("Please upload your Excel file to see all action items and enable filtering.")
