import pandas as pd
import streamlit as st

def show_ai_insights(df):
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')

    latest_date = df['Date'].max()
    previous_date = df[df['Date'] < latest_date]['Date'].max()

    # Step 1: See what dates and packages exist
    st.write("Unique dates:", df['Date'].unique())
    st.write("Unique packages:", df['Package'].unique())
    st.write("Row count for latest_date:", len(df[df['Date'] == latest_date]))
    st.write("Row count for previous_date:", len(df[df['Date'] == previous_date]))

    # Pivot to find top_package
    pivot = df.pivot_table(index=['Package'], columns='Date', values='Gross Revenue', aggfunc='sum', fill_value=0)
    if pivot.shape[1] >= 2:
        prev_day_col = previous_date
        curr_day_col = latest_date
        pivot['diff'] = pivot[curr_day_col] - pivot[prev_day_col]
        pivot['abs_diff'] = pivot['diff'].abs()
        top_package = pivot.sort_values('abs_diff', ascending=False).index[0]
        st.write("Top package:", top_package)
    else:
        top_package = df[df['Date'] == latest_date]['Package'].iloc[0]
        st.write("Fallback top_package:", top_package)

    # Show if we get rows for top_package/latest_date/previous_date
    current_rows = df[(df['Date'] == latest_date) & (df['Package'] == top_package)]
    prev_rows = df[(df['Date'] == previous_date) & (df['Package'] == top_package)]
    st.write("Current rows found:", len(current_rows))
    st.write("Previous rows found:", len(prev_rows))
    st.write("Current rows preview:", current_rows)
    st.write("Previous rows preview:", prev_rows)

    # Only proceed if BOTH exist
    if len(current_rows) > 0 and len(prev_rows) > 0:
        df_current = current_rows.iloc[0]
        df_prev = prev_rows.iloc[0]
    else:
        st.error("No data found for top package in one or both dates! Please check your data.")
        return

    # Calculate change
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
