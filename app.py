import streamlit as st
import pandas as pd
import numpy as np
from ai_insights import show_ai_insights

# --- Helper functions ---
def pct(curr, prev):
    try:
        if prev == 0:
            return 9999
        return int(round((curr - prev) / prev * 100))
    except:
        return 0

def comma(x):
    try:
        return f"{int(round(float(x))):,}"
    except:
        return x

st.set_page_config(page_title="AI-Powered Revenue Action Center", layout="wide")
st.set_page_config(page_title="AI-Powered Revenue Action Center", layout="wide")

st.markdown("# 📈 AI-Powered Revenue Action Center")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
df = None
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success(uploaded_file.name)

    # --- Clean/convert columns for dashboard ---
    for col in ['Gross Revenue', 'Revenue cost', 'eCPM', 'Publisher Impressions', 'FillRate', 'IVT (%)', 'Margin (%)']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Date handling
    df['Date'] = pd.to_datetime(df['Date'])

    # Margin calculation if not exists
    if 'Margin' not in df.columns and 'Margin (%)' in df.columns:
        df['Margin'] = df['Margin (%)']
    elif 'Margin' not in df.columns:
        df['Margin'] = ((df['Gross Revenue'] - df['Revenue cost']) / df['Gross Revenue']) * 100

    # --- Tabs ---
    tab1, tab2 = st.tabs(["Dashboard", "AI Insights"])

    with tab1:
        st.markdown("### 📊 Top 10 Grossing Packages: 3-Day Comparison")
        # Get last 6 days
        last_date = df['Date'].max()
        last_3 = sorted(df['Date'].unique())[-3:]
        prev_3 = sorted(df['Date'].unique())[-6:-3]
        df_last = df[df['Date'].isin(last_3)]
        df_prev = df[df['Date'].isin(prev_3)]
        # Top 10 by gross revenue (last 3 days)
        top10 = df_last.groupby('Package')['Gross Revenue'].sum().sort_values(ascending=False).head(10).index.tolist()
        # Build summary table
        summary = []
        for pkg in top10:
            last_rev = df_last[df_last['Package'] == pkg]['Gross Revenue'].sum()
            prev_rev = df_prev[df_prev['Package'] == pkg]['Gross Revenue'].sum()
            rev_diff = last_rev - prev_rev
            rev_pct = pct(last_rev, prev_rev)
            margin = df_last[df_last['Package'] == pkg]['Margin'].mean()
            ivt = df_last[df_last['Package'] == pkg]['IVT (%)'].mean() if 'IVT (%)' in df_last.columns else 0
            alert = ""
            if ivt >= 10:
                alert = "⚠️ High IVT"
            summary.append({
                "Package": pkg,
                "Last 3d Revenue": f"${comma(last_rev)}",
                "Prev 3d Revenue": f"${comma(prev_rev)}",
                "$ Change": f"${comma(rev_diff)}",
                "% Change": f"{rev_pct}%",
                "Margin": f"{margin:.0f}%",
                "IVT": f"{ivt:.0f}%",
                "Alert": alert
            })

        # Table header
        st.markdown(
            """
            <style>
            th, td { padding: 4px 8px !important; }
            .expand-btn { background:#eee;border:none;padding:2px 10px;border-radius:6px;margin-left:10px; }
            </style>
            """,
            unsafe_allow_html=True,
        )
        cols = st.columns([2,1,1,1,1,1,1,1,1])
        headers = ["Package", "Last 3d Revenue", "Prev 3d Revenue", "$ Change", "% Change", "Margin", "IVT", "Alert(s)", ""]
        for i, h in enumerate(headers):
            cols[i].markdown(f"**{h}**")

        # Per row: show summary and a Show More button
        for i, row in enumerate(summary):
            cols = st.columns([2,1,1,1,1,1,1,1,1])
            for j, key in enumerate(["Package", "Last 3d Revenue", "Prev 3d Revenue", "$ Change", "% Change", "Margin", "IVT", "Alert"]):
                val = row[key] if key in row else ""
                cols[j].write(val)
            expand_label = f"Show More ▾"
            show = cols[8].button(expand_label, key=f"expand_{i}")
            if show:
                # Show details breakdown below this row
                st.markdown(f"<b>Details for {row['Package']} (by Channel & Date):</b>", unsafe_allow_html=True)
                details = df[df['Package'] == row['Package']]
                details = details.sort_values(['Date','Channel'])
                det_table = details[['Date','Channel','Ad format','Gross Revenue','eCPM','FillRate','IVT (%)','Margin']]
                det_table['Date'] = det_table['Date'].dt.strftime("%d/%m")
                st.dataframe(det_table.reset_index(drop=True), use_container_width=True)

    with tab2:
        show_ai_insights(df)
else:
    st.info("Upload your Excel file to get started.")

# Helper functions
def pct(curr, prev):
    try:
        if prev == 0:
            return 9999
        return int(round((curr - prev) / prev * 100))
    except:
        return 0

def comma(x):
    try:
        return f"{int(round(float(x))):,}"
    except:
        return x
