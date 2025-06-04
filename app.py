import streamlit as st
import pandas as pd
import numpy as np

# --- Utility formatting functions ---
def comma(x):
    try:
        return f"{int(round(float(x))):,}"
    except:
        return x

def pct(old, new):
    try:
        if old == 0:
            return 9999 if new > 0 else 0
        return int(round((new - old) / old * 100))
    except:
        return 0

def format_percent(val, decimals=0):
    try:
        if np.isnan(val):
            return ''
        return f"{val:.{decimals}f}%"
    except:
        return val

def icon_dot(pct_change):
    if pct_change > 10:
        return '<span style="color:#22c55e;font-size:1.3em;">●</span>'   # green
    elif pct_change < -10:
        return '<span style="color:#ef4444;font-size:1.3em;">●</span>'  # red
    else:
        return '<span style="color:#eab308;font-size:1.3em;">●</span>'  # yellow

def margin_icon(margin):
    if margin >= 30:
        return '🟢'
    elif margin >= 20:
        return '🟡'
    else:
        return '🔴'

def ivt_icon(ivt):
    if ivt >= 10:
        return '⚠️'
    else:
        return ''

def high_ivt_alert(ivt):
    if ivt >= 10:
        return f"High IVT {ivt_icon(ivt)}"
    else:
        return ''

# --- Streamlit App ---
st.set_page_config("AI-Powered Revenue Action Center", layout="wide")
st.title("📈 AI-Powered Revenue Action Center")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Standardize column names (fix leading/trailing spaces)
    df.columns = [c.strip() for c in df.columns]

    # Make sure Date is datetime
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Fix IVT/Margin column names for code
    if 'IVT (%)' in df.columns:
        df['IVT'] = pd.to_numeric(df['IVT (%)'], errors='coerce').fillna(0)
    else:
        df['IVT'] = 0
    if 'Margin (%)' in df.columns:
        df['Margin'] = pd.to_numeric(df['Margin (%)'], errors='coerce').fillna(0)
    else:
        df['Margin'] = 0

    # --- Find latest 6 unique dates for 3+3 split ---
    date_list = sorted(df['Date'].dropna().unique())
    if len(date_list) < 6:
        st.error("Not enough days in the file. Please upload at least 6 days of data.")
        st.stop()
    last_3 = date_list[-3:]
    prev_3 = date_list[-6:-3]

    # --- Compute 3d Revenue & Stats per Package ---
    def agg3d(df, days):
        group = df[df['Date'].isin(days)].groupby('Package').agg(
            Revenue=('Gross Revenue', 'sum'),
            Margin=('Margin', 'mean'),
            IVT=('IVT', 'mean')
        ).reset_index()
        return group

    group_last = agg3d(df, last_3)
    group_prev = agg3d(df, prev_3)

    # Merge for comparison
    merged = pd.merge(group_last, group_prev, on='Package', suffixes=('_last3', '_prev3'), how='outer').fillna(0)
    merged['$ Change'] = merged['Revenue_last3'] - merged['Revenue_prev3']
    merged['% Change'] = merged.apply(lambda r: pct(r['Revenue_prev3'], r['Revenue_last3']), axis=1)

    # Add IVT, Margin icons and alerts
    merged['IVT_alert'] = merged['IVT_last3'].apply(lambda x: high_ivt_alert(x))
    merged['dot'] = merged['% Change'].apply(icon_dot)
    merged['margin_icon'] = merged['Margin_last3'].apply(margin_icon)
    merged['ivt_icon'] = merged['IVT_last3'].apply(ivt_icon)

    # --- Select top 10 by last 3d revenue ---
    merged = merged.sort_values("Revenue_last3", ascending=False).head(10).reset_index(drop=True)

    # --- Render Main Table ---
    st.markdown("### 📊 Top 10 Grossing Packages: 3-Day Comparison")
    colnames = [
        "Package", 
        f"Last 3d Revenue {pd.to_datetime(last_3[0]).strftime('%d/%m')}-{pd.to_datetime(last_3[-1]).strftime('%d/%m')}",
        f"Prev 3d Revenue {pd.to_datetime(prev_3[0]).strftime('%d/%m')}-{pd.to_datetime(prev_3[-1]).strftime('%d/%m')}",
        "$ Change", "% Change", 
        f"Margin {pd.to_datetime(last_3[0]).strftime('%d/%m')}-{pd.to_datetime(last_3[-1]).strftime('%d/%m')}",
        f"IVT {pd.to_datetime(last_3[0]).strftime('%d/%m')}-{pd.to_datetime(last_3[-1]).strftime('%d/%m')}",
        "Alert(s)"
    ]
    # Build data for display
    rows = []
    for idx, r in merged.iterrows():
        alerts = []
        if r['IVT_alert']:
            alerts.append(r['IVT_alert'])
        # Add more alerts if needed
        alert_str = " ".join(alerts)
        rows.append([
            f"🧩 {r['Package']}",
            f"${comma(r['Revenue_last3'])}",
            f"${comma(r['Revenue_prev3'])}",
            f"${comma(r['$ Change'])}",
            f"{r['% Change']}%",
            f"{int(round(r['Margin_last3']))}% {r['margin_icon']}",
            f"{int(round(r['IVT_last3']))}% {r['ivt_icon']}",
            f"{r['dot']} {alert_str}",
        ])
    # Display as HTML for sticky header
    st.markdown(
        f"""
        <style>
            .scroll-table-wrapper {{
                overflow-x: auto;
                max-width: 100%;
                margin-bottom: 1.5em;
            }}
            table.scroll-table {{
                border-collapse: collapse;
                width: 100%;
                min-width: 950px;
            }}
            table.scroll-table th, table.scroll-table td {{
                padding: 8px 10px;
                text-align: left;
                border-bottom: 1px solid #eee;
                white-space: nowrap;
            }}
            table.scroll-table th {{
                position: sticky;
                top: 0;
                background: #f7fafc;
                z-index: 2;
            }}
        </style>
        <div class="scroll-table-wrapper">
        <table class="scroll-table">
            <thead>
                <tr>
                    {''.join([f'<th>{c}</th>' for c in colnames])}
                </tr>
            </thead>
            <tbody>
                {''.join([
                    '<tr>' + ''.join([f'<td>{cell}</td>' for cell in row]) + '</tr>'
                    for row in rows
                ])}
            </tbody>
        </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Expandable Section: Channel & Date breakdown for each package ---
    st.markdown("### Show Details by Channel & Date")
    for idx, r in merged.iterrows():
        pkg = r['Package']
        with st.expander(f"Show More: {pkg}"):
            # Show breakdown by Channel and Date (sorted by revenue, descending)
            data = df[df['Package'] == pkg]
            # Only last 6 days
            data = data[data['Date'].isin(prev_3 + last_3)]
            # Group by Channel & Date
            breakdown = data.groupby(['Channel', 'Date']).agg(
                Revenue=('Gross Revenue', 'sum'),
                Margin=('Margin', 'mean'),
                IVT=('IVT', 'mean'),
                Impressions=('Publisher Impressions', 'sum'),
                eCPM=('eCPM', 'mean'),
                FillRate=('FillRate', 'mean')
            ).reset_index()
            breakdown = breakdown.sort_values(['Revenue'], ascending=False)
            if breakdown.empty:
                st.info("No breakdown data available.")
            else:
                st.markdown(
                    """
                    <style>
                        table.bd {border-collapse: collapse;width:100%;min-width:680px;}
                        table.bd th, table.bd td {padding: 5px 9px; text-align: left; border-bottom: 1px solid #f0f0f0;}
                        table.bd th {background: #f7fafc;}
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(
                    "<table class='bd'>"
                    "<thead><tr>"
                    "<th>Channel</th><th>Date</th><th>Revenue</th><th>Impr.</th><th>eCPM</th><th>Fill Rate</th><th>Margin</th><th>IVT</th>"
                    "</tr></thead><tbody>" +
                    "".join([
                        f"<tr>"
                        f"<td>{row.Channel}</td>"
                        f"<td>{row.Date.strftime('%d/%m')}</td>"
                        f"<td>${comma(row.Revenue)}</td>"
                        f"<td>{comma(row.Impressions)}</td>"
                        f"<td>{row.eCPM:.2f}</td>"
                        f"<td>{int(round(row.FillRate * 100))}%</td>"
                        f"<td>{int(round(row.Margin))}% {margin_icon(row.Margin)}</td>"
                        f"<td>{int(round(row.IVT))}% {ivt_icon(row.IVT)}</td>"
                        f"</tr>"
                        for i, row in breakdown.iterrows()
                    ])
                    + "</tbody></table>",
                    unsafe_allow_html=True,
                )

    # --- AI Chatbot Widget (Optional) ---
    st.markdown("### 💬 Ask AI About Your Data (Optional)")
    st.info("Paste your OpenAI API key to enable AI analysis (will not be saved).")
    api_key = st.text_input("Enter your OpenAI Key above to enable AI Q&A.", type="password")

else:
    st.info("Upload an Excel file to start.")
