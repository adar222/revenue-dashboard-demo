import streamlit as st
import pandas as pd
from datetime import timedelta
from ai_qna import show_ai_qna
from ai_insights import show_ai_insights

st.set_page_config(page_title="AI Revenue Action Center", layout="wide")
st.title("📈 AI-Powered Revenue Action Center")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

def colored_dot(percent):
    if percent >= 10:
        return "🟢"
    elif percent <= -10:
        return "🔴"
    else:
        return "🟡"

def comma(x):
    try:
        return f"{int(round(x)):,}"
    except:
        return x

def two_digits(x):
    try:
        return f"{x:.2f}"
    except:
        return x

def whole_percent(x):
    try:
        return f"{int(round(x))}%"
    except:
        return x

def alert_text(margin, ivt):
    alerts = []
    if margin < 25:
        alerts.append("Low Margin ❗")
    if ivt > 10:
        alerts.append("High IVT ⚠️")
    return ", ".join(alerts)

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.markdown("#### 📊 Top 10 Grossing Packages: 3-Day Comparison")

    # Data cleanup
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    df['Gross Revenue'] = pd.to_numeric(df['Gross Revenue'], errors='coerce').fillna(0)
    df['eCPM'] = pd.to_numeric(df['eCPM'], errors='coerce').fillna(0)
    df['FillRate'] = pd.to_numeric(df['FillRate'], errors='coerce').fillna(0)
    df['IVT'] = pd.to_numeric(df['IVT'], errors='coerce').fillna(0)
    df['Margin'] = pd.to_numeric(df.get('Margin', (df['Gross Revenue']-0)/df['Gross Revenue']*100), errors='coerce').fillna(0)

    last_day = df['Date'].max()
    prev_end = last_day - timedelta(days=3)
    prev_start = prev_end - timedelta(days=2)

    # Last 3d and previous 3d
    mask_last3d = (df['Date'] > prev_end) & (df['Date'] <= last_day)
    mask_prev3d = (df['Date'] > prev_start - timedelta(days=1)) & (df['Date'] <= prev_end)
    df_last3d = df[mask_last3d]
    df_prev3d = df[mask_prev3d]

    # Aggregated by package
    agg_last = df_last3d.groupby('Package').agg({
        'Gross Revenue': 'sum',
        'Margin': 'mean',
        'IVT': 'mean'
    }).rename(columns={
        'Gross Revenue': 'Last 3d Revenue',
        'Margin': 'Margin 3d',
        'IVT': 'IVT 3d'
    })
    agg_prev = df_prev3d.groupby('Package').agg({
        'Gross Revenue': 'sum'
    }).rename(columns={'Gross Revenue': 'Prev 3d Revenue'})

    merged = agg_last.join(agg_prev, how='left')
    merged['Prev 3d Revenue'] = merged['Prev 3d Revenue'].fillna(0)
    merged['$ Change'] = merged['Last 3d Revenue'] - merged['Prev 3d Revenue']
    merged['% Change'] = merged.apply(lambda row: (row['$ Change'] / row['Prev 3d Revenue'] * 100) if row['Prev 3d Revenue'] > 0 else 9999, axis=1)
    merged['Alert(s)'] = merged.apply(lambda row: alert_text(row['Margin 3d'], row['IVT 3d']), axis=1)
    merged['Dot'] = merged['% Change'].apply(colored_dot)
    merged = merged.sort_values('Last 3d Revenue', ascending=False).head(10).reset_index()

    # Main Table header
    st.markdown("""
    <style>
    .freeze-header th { position: sticky; top: 0; background-color: #fff; z-index: 5;}
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div style="overflow-x:auto;">', unsafe_allow_html=True)

    # Show table header (frozen via CSS)
    st.write(" ")
    header_row = [
        "Package",
        f"Last 3d Revenue {last_day.strftime('%d/%m')}",
        f"Prev 3d Revenue {(prev_end).strftime('%d/%m')}",
        "$ Change", "% Change", 
        f"Margin {last_day.strftime('%d/%m')}",
        f"IVT {last_day.strftime('%d/%m')}",
        "Alert(s)"
    ]
    table_data = []
    for idx, row in merged.iterrows():
        pkg = row['Package']
        alerts = row['Alert(s)']
        dot = row['Dot']
        table_data.append([
            f"{pkg} {dot}",
            f"${comma(row['Last 3d Revenue'])}",
            f"${comma(row['Prev 3d Revenue'])}",
            f"${comma(row['$ Change'])}",
            f"{int(row['% Change']) if abs(row['% Change']) != 9999 else '--'}%",
            whole_percent(row['Margin 3d']),
            whole_percent(row['IVT 3d']),
            alerts
        ])

    st.table(pd.DataFrame(table_data, columns=header_row))

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### Show Details by Channel & Date")

    for idx, row in merged.iterrows():
        pkg = row['Package']
        with st.expander(f"Show More: {pkg}", expanded=False):
            # Show breakdown by channel and date
            subset = df[df['Package'] == pkg]
            if not subset.empty:
                detail_table = subset.groupby(['Channel', 'Date']).agg({
                    'Gross Revenue': 'sum',
                    'eCPM': 'mean',
                    'FillRate': 'mean',
                    'IVT': 'mean',
                    'Margin': 'mean'
                }).reset_index().sort_values('Gross Revenue', ascending=False)
                detail_table['Date'] = detail_table['Date'].dt.strftime('%d/%m')
                detail_table['Gross Revenue'] = detail_table['Gross Revenue'].apply(lambda x: f"${comma(x)}")
                detail_table['eCPM'] = detail_table['eCPM'].apply(two_digits)
                detail_table['FillRate'] = detail_table['FillRate'].apply(lambda x: f"{int(round(x))}%")
                detail_table['IVT'] = detail_table['IVT'].apply(lambda x: f"{int(round(x))}%")
                detail_table['Margin'] = detail_table['Margin'].apply(whole_percent)
                st.dataframe(detail_table, use_container_width=True)
            else:
                st.info("No channel/date data for this package.")

    # AI Q&A
    st.markdown("## 💬 Ask AI About Your Data (Optional)")
    api_key = st.text_input("Paste your OpenAI API key to enable AI analysis (will not be saved):", type="password")
    if api_key:
        show_ai_qna(df, api_key)
    else:
        st.info("Enter your OpenAI API key above to enable AI Q&A.")

    # Tab for AI Insights
    st.markdown("---")
    st.markdown("### See also: AI Insights (top navigation)")

else:
    st.info("Please upload your Excel file to see all action items and enable filtering.")
