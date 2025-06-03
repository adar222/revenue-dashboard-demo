import pandas as pd
import streamlit as st

def pct(curr, prev):
    try:
        if prev == 0:
            return 9999
        return int(round((curr - prev) / prev * 100))
    except:
        return 0

def clean_num(val):
    if pd.isnull(val):
        return 0
    val = str(val).replace('$','').replace(',','').replace('%','').strip()
    try:
        return float(val)
    except:
        return 0

def show_ai_insights(df):
    # --- Data Cleaning ---
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')

    df['Gross Revenue'] = df['Gross Revenue'].apply(clean_num)
    df['Revenue cost'] = df['Revenue cost'].apply(clean_num)
    df['eCPM'] = df['eCPM'].apply(clean_num)
    df['Publisher Impressions'] = df['Publisher Impressions'].apply(clean_num)
    df['FillRate'] = df['FillRate'].astype(str).str.replace('%','').astype(float) # Already in percent
    # Don't divide FillRate by 100!

    # Margin calculation
    df['Margin'] = ((df['Gross Revenue'] - df['Revenue cost']) / df['Gross Revenue']) * 100

    latest_date = df['Date'].max()
    previous_date = df[df['Date'] < latest_date]['Date'].max()

    # Top 10 by Gross Revenue for latest_date
    latest = df[df['Date'] == latest_date].copy()
    prev = df[df['Date'] == previous_date].copy()

    top10 = latest.sort_values('Gross Revenue', ascending=False).head(10)
    
    st.subheader(f"Top 10 Packages by Gross Revenue – {latest_date.strftime('%Y-%m-%d')}")
    for _, row in top10.iterrows():
        pkg = row['Package']
        prev_row = prev[prev['Package'] == pkg]
        if not prev_row.empty:
            prev_row = prev_row.iloc[0]
            rev_change = pct(row['Gross Revenue'], prev_row['Gross Revenue'])
            margin_today = row['Margin']
            margin_prev = prev_row['Margin']
            main_driver = ""
            # Drivers: eCPM, FillRate, Imps (find biggest change %)
            driver_candidates = [
                ('eCPM', pct(row['eCPM'], prev_row['eCPM'])),
                ('Fill Rate', pct(row['FillRate'], prev_row['FillRate'])),
                ('Impressions', pct(row['Publisher Impressions'], prev_row['Publisher Impressions'])),
            ]
            main_metric, main_change = max(driver_candidates, key=lambda x: abs(x[1]))
            main_driver = f"{main_metric} {'up' if main_change > 0 else 'down'} {abs(main_change)}%"

            color = "#22B573" if rev_change > 0 else "#e74c3c"
            sign = "+" if rev_change > 0 else ""
            st.markdown(
                f"**{pkg} ({row['Ad format']})**  \n"
                f"Revenue: <b>{int(row['Gross Revenue']):,}</b> ({latest_date.strftime('%Y-%m-%d')}) | "
                f"<b>{int(prev_row['Gross Revenue']):,}</b> ({previous_date.strftime('%Y-%m-%d')}) "
                f"<span style='color:{color};font-weight:bold;'>[{sign}{rev_change}%]</span>  \n"
                f"Margin: {margin_today:.2f}% ({latest_date.strftime('%Y-%m-%d')}) | {margin_prev:.2f}% ({previous_date.strftime('%Y-%m-%d')})  \n"
                f"Main driver: {main_driver}  \n"
                f"eCPM: {row['eCPM']:.2f} ➡️ {prev_row['eCPM']:.2f}  \n"
                f"Fill Rate: {row['FillRate']:.2f}% ➡️ {prev_row['FillRate']:.2f}%  \n"
                f"Imps: {int(row['Publisher Impressions']):,} ➡️ {int(prev_row['Publisher Impressions']):,}",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"**{pkg} ({row['Ad format']})**  \n"
                f"Revenue: <b>{int(row['Gross Revenue']):,}</b> ({latest_date.strftime('%Y-%m-%d')}) | "
                f"No data for previous date."
            )
        st.markdown("---")
