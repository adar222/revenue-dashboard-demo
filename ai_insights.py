import streamlit as st
import pandas as pd

def show_ai_insights(df):
    st.header("🤖 AI Insights: Top Revenue Changes (Biggest Movers)")

    # Ensure correct types and sorting
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(['Package', 'Date'])

    group_cols = ['Advertiser', 'Ad format', 'Channel', 'Package']

    # Calculate day-over-day % changes and previous day values
    df['Gross Revenue Change %'] = df.groupby(group_cols)['Gross Revenue'].pct_change() * 100
    df['Prev Gross Revenue'] = df.groupby(group_cols)['Gross Revenue'].shift(1)
    df['FillRate Change %'] = df.groupby(group_cols)['FillRate'].pct_change() * 100
    df['Prev FillRate'] = df.groupby(group_cols)['FillRate'].shift(1)
    df['eCPM Change %'] = df.groupby(group_cols)['eCPM'].pct_change() * 100
    df['Prev eCPM'] = df.groupby(group_cols)['eCPM'].shift(1)

    # Filter for changes above 20% (increase or decrease)
    movers = df[df['Gross Revenue Change %'].abs() > 20].copy()

    # Separate increases and decreases
    increases = movers[movers['Gross Revenue Change %'] > 0].sort_values('Gross Revenue Change %', ascending=False).head(8)
    decreases = movers[movers['Gross Revenue Change %'] < 0].sort_values('Gross Revenue Change %').head(8)

    # Combine for display
    display_movers = pd.concat([increases, decreases])

    if display_movers.empty:
        st.info("No significant revenue movers (>20%) detected.")
        return

    # For each mover, show a detailed card
    for idx, row in display_movers.iterrows():
        # Get package info
        package = row['Package']
        channel = row['Channel']
        ad_format = row['Ad format']
        advertiser = row['Advertiser']
        date = row['Date'].date()

        curr_rev = row['Gross Revenue']
        prev_rev = row['Prev Gross Revenue']

        curr_fill = row['FillRate']
        prev_fill = row['Prev FillRate']

        curr_ecpm = row['eCPM']
        prev_ecpm = row['Prev eCPM']

        # Severity badge & color
        pct = row['Gross Revenue Change %']
        is_up = pct > 0
        severity = "Critical Change" if abs(pct) >= 50 else ("Medium" if abs(pct) >= 35 else "Minor")
        badge = "🔥" if abs(pct) >= 50 else ("⚠️" if abs(pct) >= 35 else "🟢")
        color = "green" if is_up else "red"
        direction_word = "increased" if is_up else "dropped"

        # Headline
        st.markdown(f"#### {badge} <span style='color:{color}; font-size:1.2em;'><b>{package}</b></span> ({channel} - {ad_format})", unsafe_allow_html=True)
        st.markdown(
            f"<b>{date}</b>: <span style='color:{color};'>Gross Revenue {direction_word} by {abs(pct):.1f}%</span> "
            f"(from <b>${prev_rev:,.0f}</b> to <b>${curr_rev:,.0f}</b>)", unsafe_allow_html=True
        )

        # Side-by-side cards
        colA, colArrow, colB, colSeverity = st.columns([3, 1, 3, 2])
        with colA:
            st.write("**Previous Day**")
            st.write(f"Date: {date}")
            st.write(f"Gross Revenue: ${prev_rev:,.0f}")
            st.write(f"eCPM: ${prev_ecpm:.2f}")
            st.write(f"Fill Rate: {prev_fill:.2%}")
        with colArrow:
            st.markdown(f"<div style='font-size:2em; color:{color}; text-align:center;'>➡️</div>", unsafe_allow_html=True)
        with colB:
            st.write("**Current Day**")
            st.write(f"Date: {row['Date'].date()}")
            st.write(f"Gross Revenue: ${curr_rev:,.0f}")
            st.write(f"eCPM: ${curr_ecpm:.2f}")
            st.write(f"Fill Rate: {curr_fill:.2%}")
        with colSeverity:
            st.write("**Impact**")
            st.markdown(f"<span style='font-size:2em;'>{badge}</span>", unsafe_allow_html=True)
            st.write(severity)

        # Mini 7-day trendline for this package
        pkg_mask = (
            (df['Package'] == package) &
            (df['Channel'] == channel) &
            (df['Ad format'] == ad_format) &
            (df['Advertiser'] == advertiser)
        )
        trend = df.loc[pkg_mask, ['Date', 'Gross Revenue']].sort_values('Date').tail(7)
        st.write("**7-Day Revenue Trend**")
        st.line_chart(trend.set_index('Date'))

        # Possible reasons with numbers
        reasons = []
        # eCPM reason
        if abs(row['eCPM Change %']) > 10 and not pd.isnull(prev_ecpm):
            ecpmdir = "increased" if row['eCPM Change %'] > 0 else "dropped"
            reasons.append(f"eCPM {ecpmdir} by {abs(row['eCPM Change %']):.1f}% (from ${prev_ecpm:.2f} to ${curr_ecpm:.2f})")
        # FillRate reason
        if abs(row['FillRate Change %']) > 10 and not pd.isnull(prev_fill):
            filldir = "increased" if row['FillRate Change %'] > 0 else "dropped"
            reasons.append(f"Fill Rate {filldir} by {abs(row['FillRate Change %']):.1f}% (from {prev_fill:.2%} to {curr_fill:.2%})")
        # Add more metrics as needed

        if reasons:
            st.write("**Possible reasons:**")
            for r in reasons:
                st.write(f"- {r}")
        else:
            st.write("No significant related metric changes detected.")

        # Show Raw Data button
        with st.expander("Show Raw Data (last 7 days for this package)"):
            st.dataframe(trend)

        st.markdown("---")
