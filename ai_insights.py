import pandas as pd
import streamlit as st

def show_ai_insights(df):
    # Convert Date to datetime
    df['Date'] = pd.to_datetime(df['Date'])

    # Sort by date (just in case)
    df = df.sort_values('Date')

    # Find latest date and previous date with data
    latest_date = df['Date'].max()
    previous_date = df[df['Date'] < latest_date]['Date'].max()

    # Get "current day" and "previous day" row for the TOP revenue package
    # Here we use the package with the largest revenue change (absolute value)
    pivot = df.pivot_table(index=['Package'], columns='Date', values='Gross Revenue', aggfunc='sum', fill_value=0)
    if pivot.shape[1] >= 2:
        prev_day_col = previous_date
        curr_day_col = latest_date
        pivot['diff'] = pivot[curr_day_col] - pivot[prev_day_col]
        pivot['abs_diff'] = pivot['diff'].abs()
        top_package = pivot.sort_values('abs_diff', ascending=False).index[0]
        df_current = df[(df['Date'] == latest_date) & (df['Package'] == top_package)].iloc[0]
        df_prev = df[(df['Date'] == previous_date) & (df['Package'] == top_package)].iloc[0]
    else:
        # Fallback: just pick first
        df_current = df[df['Date'] == latest_date].iloc[0]
        df_prev = df[df['Date'] == previous_date].iloc[0]
        top_package = df_current['Package']

    # Calculate % change
    prev_rev = df_prev['Gross Revenue']
    curr_rev = df_current['Gross Revenue']
    if prev_rev != 0:
        growth = ((curr_rev - prev_rev) / prev_rev * 100)
    else:
        growth = float('inf')

    # Card display
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
