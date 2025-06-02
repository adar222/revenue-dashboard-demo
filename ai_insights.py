import streamlit as st
import pandas as pd

def show_ai_insights(df):
    st.header("🤖 AI Insights: Biggest Changes in Performance")

    # Ensure correct types
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(['Package', 'Date'])

    # Calculate day-over-day % change for Gross Revenue and other metrics
    group_cols = ['Advertiser', 'Ad format', 'Channel', 'Package']
    df['Gross Revenue Change %'] = df.groupby(group_cols)['Gross Revenue'].pct_change() * 100
    df['FillRate Change %'] = df.groupby(group_cols)['FillRate'].pct_change() * 100
    df['eCPM Change %'] = df.groupby(group_cols)['eCPM'].pct_change() * 100
    df['Publisher Impressions Change %'] = df.groupby(group_cols)['Publisher Impressions'].pct_change() * 100

    # Filter for changes above 20% (either direction)
    mask = df['Gross Revenue Change %'].abs() > 20
    insights = df[mask].copy()
    insights = insights.sort_values('Gross Revenue Change %', key=abs, ascending=False)

    if insights.empty:
        st.info("No changes above 20% detected for the selected period.")
        return

    for idx, row in insights.iterrows():
        change = row['Gross Revenue Change %']
        direction = "increased" if change > 0 else "dropped"
        st.markdown(f"### 📦 {row['Package']} ({row['Channel']} - {row['Ad format']})")
        st.write(f"On {row['Date'].date()}, Gross Revenue **{direction} by {abs(change):.1f}%** "
                 f"(from previous day).")
        # Explanation logic—feel free to expand!
        details = []
        if abs(row['FillRate Change %']) > 10:
            details.append(f"FillRate {('increased' if row['FillRate Change %'] > 0 else 'dropped')} by {abs(row['FillRate Change %']):.1f}%")
        if abs(row['eCPM Change %']) > 10:
            details.append(f"eCPM {('increased' if row['eCPM Change %'] > 0 else 'dropped')} by {abs(row['eCPM Change %']):.1f}%")
        if abs(row['Publisher Impressions Change %']) > 10:
            details.append(f"Publisher Impressions {('increased' if row['Publisher Impressions Change %'] > 0 else 'dropped')} by {abs(row['Publisher Impressions Change %']):.1f}%")
        if details:
            st.write("Possible reasons:")
            for d in details:
                st.write(f"- {d}")
        else:
            st.write("No significant related metric changes detected.")
        st.markdown("---")
