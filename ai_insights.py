import streamlit as st
import pandas as pd

def show_ai_insights(df):
    # ---- Logic for Current/Previous Day ----
    df['Date'] = pd.to_datetime(df['Date'])
    latest_date = df['Date'].max()
    previous_date = df[df['Date'] < latest_date]['Date'].max()

    df_current = df[df['Date'] == latest_date].iloc[0]
    df_prev = df[df['Date'] == previous_date].iloc[0]

    # ---- Calculate Change ----
    growth = ((df_current["Gross Revenue"] - df_prev["Gross Revenue"]) / df_prev["Gross Revenue"]) * 100 if df_prev["Gross Revenue"] > 0 else float('inf')

    # ---- Render Card ----
    st.header("🤖 AI Insights: Top Revenue Changes (Biggest Movers)")
    st.markdown(
        f"""
        <span style="color:#22B573;font-size:20px;"><b>🔥 paint.by.number.pixel.art.coloring.drawing.puzzle (wbe - RICH_TEXT)</b></span>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <span style="font-size:16px;">
        <b>{latest_date.strftime('%Y-%m-%d')}</b>: Gross Revenue increased by <b>{growth:.1f}%</b>
        (from <b>${df_prev["Gross Revenue"]}</b> to <b>${df_current["Gross Revenue"]}</b>)
        </span>
        """,
        unsafe_allow_html=True
    )

    cols = st.columns([2, 2, 1, 2])

    with cols[0]:
        st.markdown("#### Previous Day")
        st.write(f"Date: {previous_date.strftime('%Y-%m-%d')}")
        st.write(f"Gross Revenue: ${df_prev['Gross Revenue']}")
        st.write(f"eCPM: ${df_prev['eCPM']}")
        st.write(f"Fill Rate: {df_prev['Fill Rate']}%")

    with cols[1]:
        st.markdown("#### Current Day")
        st.write(f"Date: {latest_date.strftime('%Y-%m-%d')}")
        st.write(f"Gross Revenue: ${df_current['Gross Revenue']}")
        st.write(f"eCPM: ${df_current['eCPM']}")
        st.write(f"Fill Rate: {df_current['Fill Rate']}%")

    with cols[2]:
        st.write("")
        st.write("➡️")

    with cols[3]:
        st.markdown("#### Impact")
        st.markdown("🔥 Critical Change")

    st.markdown("---")
