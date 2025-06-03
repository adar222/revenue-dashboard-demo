import pandas as pd
import streamlit as st

def show_ai_insights(df):
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')

    latest_date = df['Date'].max()
    previous_date = df[df['Date'] < latest_date]['Date'].max()

    # Only keep packages that appear in BOTH dates
    packages_latest = set(df[df['Date'] == latest_date]['Package'])
    packages_prev = set(df[df['Date'] == previous_date]['Package'])
    valid_packages = packages_latest & packages_prev

    if not valid_packages:
        st.warning("No packages found with data for both the latest and previous dates.")
        return

    # Compute absolute revenue change for these packages
    rev_changes = []
    for pkg in valid_packages:
        curr_row = df[(df['Date'] == latest_date) & (df['Package'] == pkg)].iloc[0]
        prev_row = df[(df['Date'] == previous_date) & (df['Package'] == pkg)].iloc[0]
        change = abs(curr_row['Gross Revenue'] - prev_row['Gross Revenue'])
        rev_changes.append((pkg, change))

    # Pick package with biggest absolute change
    top_package = sorted(rev_changes, key=lambda x: -x[1])[0][0]

    df_current = df[(df['Date'] == latest_date) & (df['Package'] == top_package)].iloc[0]
    df_prev = df[(df['Date'] == previous_date) & (df['Package'] == top_package)].iloc[0]

    # Calculate % change
    prev_rev = df_prev['Gross Revenue']
    curr_rev = df_current['Gross Revenue']
    growth = ((curr_rev - prev_rev) / prev_rev * 100) if prev_rev != 0 else float('inf')

    st.header("🤖 AI Insights: Top Revenue Changes (Biggest Movers)")
    st.markdown(
        f"""
        <span style="color:#22B573;font-size:20px;"><b>🔥 {df_current['Package']} ({df_current['Ad format']})</b></span>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        f"""
        <span style="font-size:16px;">
        <b>{latest_date.strftime('%Y-%m-%d')}</b>: Gross Revenue changed by <b>{growth:.1f}%</b>
        (from <b>${prev_rev:.2f}</b> to <b>${curr_rev:.2f}</b>)
        </span>
        """,
        unsafe_allow_html=True
    )

    cols = st.columns([2, 2, 1, 2])
    with cols[0]:
        st.markdown("#### Previous Day")
        st.write(f"Date: {previous_date.strftime('%Y-%m-%d')}")
        st.write(f"Gross Revenue: ${df_prev['Gross Revenue']:.2f}")
        st.write(f"eCPM: ${df_prev['eCPM']:.2f}")
        st.write(f"Fill Rate: {df_prev['FillRate']:.2%}")
    with cols[1]:
        st.markdown("#### Current Day")
        st.write(f"Date: {latest_date.strftime('%Y-%m-%d')}")
        st.write(f"Gross Revenue: ${df_current['Gross Revenue']:.2f}")
        st.write(f"eCPM: ${df_current['eCPM']:.2f}")
        st.write(f"Fill Rate: {df_current['FillRate']:.2%}")
    with cols[2]:
        st.write("")
        st.write("➡️")
    with cols[3]:
        st.markdown("#### Impact")
        st.markdown("🔥 Critical Change")
    st.markdown("---")
