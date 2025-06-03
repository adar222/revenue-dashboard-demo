import streamlit as st
import pandas as pd
from action_center import show_action_center_top10, show_dropped_channels, show_best_worst_formats
from ai_qna import show_ai_qna
from ai_insights import show_ai_insights
from datetime import timedelta

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

def alert_text(margin, ivt):
    alerts = []
    if margin < 25:
        alerts.append("**Low Margin**")
    if ivt > 10:
        alerts.append("**High IVT**")
    return ", ".join(alerts)

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # ---- SANITY CHECK START ----
    required_columns = [
        'Date', 'Package', 'Gross Revenue', 'eCPM', 'FillRate',
        'Publisher Impressions', 'Ad format'
    ]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        st.error(f"ERROR: The following required columns are missing from your Excel: {', '.join(missing)}")
        st.stop()
    # ---- SANITY CHECK END ----

    # --- Prepare dates for 3-day rolling windows ---
    df['Date'] = pd.to_datetime(df['Date'])
    latest_day = df['Date'].max()
    prev_window_end = latest_day - timedelta(days=3)
    prev_window_start = latest_day - timedelta(days=5)
    curr_window = (df['Date'] > prev_window_end)
    prev_window = (df['Date'] >= prev_window_start) & (df['Date'] <= prev_window_end)

    curr_dates = df.loc[curr_window, 'Date'].dt.strftime('%d/%m').unique()
    prev_dates = df.loc[prev_window, 'Date'].dt.strftime('%d/%m').unique()
    curr_dates_str = f"{curr_dates[0]}-{curr_dates[-1]}" if len(curr_dates) > 1 else f"{curr_dates[0]}"
    prev_dates_str = f"{prev_dates[0]}-{prev_dates[-1]}" if len(prev_dates) > 1 else f"{prev_dates[0]}"

    tab1, tab2 = st.tabs(["Dashboard", "AI Insights"])

    with tab1:
        st.markdown("#### 🚦 Top 10 Grossing Packages: 3-Day Comparison")

        # Aggregate revenue for each window, per package
        grp_cols = ['Package']
        agg_cols = {
            'Gross Revenue': 'sum',
            'Margin (%)': 'mean',
            'IVT (%)': 'mean'
        }
        last3 = df[curr_window].groupby(grp_cols).agg(agg_cols).rename(
            columns={
                'Gross Revenue': 'last3_revenue',
                'Margin (%)': 'last3_margin',
                'IVT (%)': 'last3_ivt'
            }
        )
        prev3 = df[prev_window].groupby(grp_cols).agg(agg_cols).rename(
            columns={
                'Gross Revenue': 'prev3_revenue',
                'Margin (%)': 'prev3_margin',
                'IVT (%)': 'prev3_ivt'
            }
        )

        merged = last3.merge(prev3, left_index=True, right_index=True, how='outer').fillna(0)
        merged['$ Change'] = merged['last3_revenue'] - merged['prev3_revenue']
        merged['% Change'] = ((merged['last3_revenue'] - merged['prev3_revenue']) / merged['prev3_revenue'].replace(0, 1)) * 100

        # Order by last 3 days revenue (top 10)
        merged = merged.sort_values('last3_revenue', ascending=False).head(10)

        # Reset index for iteration
        merged = merged.reset_index()

        # Build column headers with dates
        col_labels = [
            "Package",
            f"Last 3d Revenue\n:blue[{curr_dates_str}]",
            f"Prev 3d Revenue\n:gray[{prev_dates_str}]",
            "$ Change",
            "% Change",
            f"Margin\n:blue[{curr_dates_str}]",
            f"IVT\n:blue[{curr_dates_str}]",
            "Alert(s)",
            "Show More"
        ]

        # Show formatted table with expanders per row
        for idx, row in merged.iterrows():
            pkg = row['Package']
            last3_rev = row['last3_revenue']
            prev3_rev = row['prev3_revenue']
            dollar_change = row['$ Change']
            pct_change = row['% Change']
            last3_margin = row['last3_margin']
            last3_ivt = row['last3_ivt']

            dot = colored_dot(pct_change)
            alerts = alert_text(last3_margin, last3_ivt)

            cols = st.columns([2.8, 2.3, 2.3, 1.5, 1.5, 1.5, 1.2, 2, 1.5])
            cols[0].markdown(f"**{pkg}**")
            cols[1].markdown(f"${last3_rev:,.0f}")
            cols[2].markdown(f"${prev3_rev:,.0f}")
            cols[3].markdown(f"{'+' if dollar_change >=0 else ''}${dollar_change:,.0f}")
            cols[4].markdown(f"{'+' if pct_change >=0 else ''}{pct_change:.0f}%")
            cols[5].markdown(f"{int(round(last3_margin))}%")
            cols[6].markdown(f"{int(round(last3_ivt))}%")
            alert_str = f"{dot}"
            if alerts:
                alert_str += f" {alerts}"
            cols[7].markdown(alert_str)
            with cols[8]:
                with st.expander("Show More", expanded=False):
                    # Breakdown by Channel and Date for this package (last 6 days)
                    recent = df[(df['Package'] == pkg) & (df['Date'] >= prev_window_start)]
                    if not recent.empty:
                        breakdown = recent.groupby(['Channel', 'Date']).agg({
                            'Gross Revenue': 'sum',
                            'eCPM': 'mean',
                            'IVT (%)': 'mean',
                            'Margin (%)': 'mean'
                        }).reset_index()
                        # Formatting
                        breakdown['Gross Revenue'] = breakdown['Gross Revenue'].apply(lambda x: f"${x:,.0f}")
                        breakdown['Date'] = breakdown['Date'].dt.strftime('%d/%m')
                        breakdown['eCPM'] = breakdown['eCPM'].apply(lambda x: f"{x:.2f}")
                        breakdown['IVT (%)'] = breakdown['IVT (%)'].apply(lambda x: f"{int(round(x))}%")
                        breakdown['Margin (%)'] = breakdown['Margin (%)'].apply(lambda x: f"{int(round(x))}%")
                        st.dataframe(breakdown, use_container_width=True, height=230)
                    else:
                        st.write("No data available for this package in last 6 days.")

            st.markdown("---")

        st.markdown("## 💬 Ask AI About Your Data (Optional)")
        api_key = st.text_input("Paste your OpenAI API key to enable AI analysis (will not be saved):", type="password", key="api_key_tab1")
        if api_key:
            show_ai_qna(df, api_key)
        else:
            st.info("Enter your OpenAI API key above to enable AI Q&A.")

    with tab2:
        show_ai_insights(df)
        st.markdown("---")
        st.markdown("## 💬 Ask AI About Your Data (Optional)")
        api_key2 = st.text_input("Paste your OpenAI API key to enable AI analysis (will not be saved):", type="password", key="api_key_tab2")
        if api_key2:
            show_ai_qna(df, api_key2)
        else:
            st.info("Enter your OpenAI API key above to enable AI Q&A.")

else:
    st.info("Please upload your Excel file to see all action items and enable filtering.")
