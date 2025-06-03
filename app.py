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

def trend_dot(rev_pct):
    if rev_pct > 10:
        return "🟢"
    elif rev_pct < -10:
        return "🔴"
    else:
        return "🟡"

def color_pct(val):
    if val > 10:
        return f"<span style='color: #228B22; font-weight: bold;'>{val}%</span>"  # green
    elif val < -10:
        return f"<span style='color: #e74c3c; font-weight: bold;'>{val}%</span>"  # red
    else:
        return f"<span style='color: #e1bc29; font-weight: bold;'>{val}%</span>"  # yellow

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
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
    else:
        st.error("Date column missing from your file.")
        st.stop()

    # Margin calculation if not exists
    if 'Margin' not in df.columns:
        if 'Margin (%)' in df.columns:
            df['Margin'] = df['Margin (%)']
        elif 'Gross Revenue' in df.columns and 'Revenue cost' in df.columns:
            df['Margin'] = ((df['Gross Revenue'] - df['Revenue cost']) / df['Gross Revenue']) * 100
        else:
            df['Margin'] = 0

    # --- Tabs ---
    tab1, tab2 = st.tabs(["Dashboard", "AI Insights"])

    with tab1:
        st.markdown("### 📊 Top 10 Grossing Packages: 3-Day Comparison")

        # Get last 6 days (if enough days exist)
        try:
            date_list = sorted(df['Date'].unique())
            if len(date_list) < 6:
                st.error("You need at least 6 days of data in your file for the 3-day comparison.")
                st.stop()
            last_3 = date_list[-3:]
            prev_3 = date_list[-6:-3]
        except Exception as e:
            st.error("Date parsing error. Please check your Date column format.")
            st.stop()

        df_last = df[df['Date'].isin(last_3)]
        df_prev = df[df['Date'].isin(prev_3)]

        # Top 10 by gross revenue (last 3 days)
        if 'Gross Revenue' not in df.columns or 'Package' not in df.columns:
            st.error("Missing 'Gross Revenue' or 'Package' columns.")
            st.stop()

        top10 = df_last.groupby('Package')['Gross Revenue'].sum().sort_values(ascending=False).head(10).index.tolist()

        # Table header
        st.markdown(
            """
            <style>
            th, td { padding: 4px 8px !important; }
            .expand-btn { background:#eee;border:none;padding:2px 10px;border-radius:6px;margin-left:10px; }
            .frozen-header thead th { position: sticky; top: 0; background: #fafbfc; z-index: 1; }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Build summary table data
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
                "% Change": rev_pct,
                "Margin": f"{margin:.0f}%",
                "IVT": f"{ivt:.0f}%",
                "Alert": alert,
                "Dot": trend_dot(rev_pct),
            })

        # Custom table with icons/colors
        headers = ["", "Package", "Last 3d Revenue", "Prev 3d Revenue", "$ Change", "% Change", "Margin", "IVT", "Alert(s)", ""]
        cols = st.columns([0.5,2,1,1,1,1,1,1,1,1])
        for i, h in enumerate(headers):
            if h == "% Change":
                cols[i].markdown(f"<b>{h}</b>", unsafe_allow_html=True)
            else:
                cols[i].markdown(f"**{h}**")

        for i, row in enumerate(summary):
            cols = st.columns([0.5,2,1,1,1,1,1,1,1,1])
            # Dot icon
            cols[0].markdown(row["Dot"])
            # Package
            cols[1].markdown(f"📱 <b>{row['Package']}</b>", unsafe_allow_html=True)
            # Revenue columns
            cols[2].markdown(row["Last 3d Revenue"])
            cols[3].markdown(row["Prev 3d Revenue"])
            cols[4].markdown(row["$ Change"])
            # % Change with color
            cols[5].markdown(color_pct(row["% Change"]), unsafe_allow_html=True)
            # Margin/IVT/Alert
            cols[6].markdown(row["Margin"])
            cols[7].markdown(row["IVT"])
            cols[8].markdown(row["Alert"])
            # Show more
            show = cols[9].button("Show More", key=f"expand_{i}")
            if show:
                st.markdown(f"<b>Details for {row['Package']} (by Channel & Date):</b>", unsafe_allow_html=True)
                details = df[df['Package'] == row['Package']]
                details = details.sort_values(['Date','Channel'])
                det_table = details[['Date','Channel','Ad format','Gross Revenue','eCPM','FillRate','IVT (%)','Margin']].copy()
                det_table['Date'] = det_table['Date'].dt.strftime("%d/%m")
                det_table['Gross Revenue'] = det_table['Gross Revenue'].apply(comma)
                det_table['eCPM'] = det_table['eCPM'].apply(lambda x: f"{x:.2f}")
                det_table['FillRate'] = det_table['FillRate'].apply(lambda x: f"{x:.0f}%")
                det_table['IVT (%)'] = det_table['IVT (%)'].apply(lambda x: f"{x:.0f}%")
                det_table['Margin'] = det_table['Margin'].apply(lambda x: f"{x:.0f}%")
                st.dataframe(det_table.reset_index(drop=True), use_container_width=True)

    with tab2:
        show_ai_insights(df)
else:
    st.info("Upload your Excel file to get started.")
