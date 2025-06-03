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

def margin_icon(margin):
    if margin >= 40:
        return "✅"
    elif margin < 25:
        return "❗"
    else:
        return ""

def ivt_icon(ivt):
    if ivt > 10:
        return "⚠️"
    else:
        return ""

def alert_text(margin, ivt):
    alerts = []
    if margin < 25:
        alerts.append("Low Margin ❗")
    if ivt > 10:
        alerts.append("High IVT ⚠️")
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
        merged = merged.reset_index()

        # Prepare summary DataFrame with icons/colors as text
        summary_rows = []
        for idx, row in merged.iterrows():
            pkg = row['Package']
            last3_rev = f"${row['last3_revenue']:,.0f}"
            prev3_rev = f"${row['prev3_revenue']:,.0f}"
            dollar_change = f"{'+' if row['$ Change'] >= 0 else ''}${row['$ Change']:,.0f}"
            pct_change = f"{'+' if row['% Change'] >= 0 else ''}{row['% Change']:.0f}%"
            margin = f"{int(round(row['last3_margin']))}% {margin_icon(row['last3_margin'])}"
            ivt = f"{int(round(row['last3_ivt']))}% {ivt_icon(row['last3_ivt'])}"
            alerts = f"{colored_dot(row['% Change'])} {alert_text(row['last3_margin'], row['last3_ivt'])}"
            summary_rows.append([pkg, last3_rev, prev3_rev, dollar_change, pct_change, margin, ivt, alerts])

        summary_df = pd.DataFrame(
            summary_rows,
            columns=[
                "Package",
                f"Last 3d Revenue\n{curr_dates_str}",
                f"Prev 3d Revenue\n{prev_dates_str}",
                "$ Change",
                "% Change",
                f"Margin\n{curr_dates_str}",
                f"IVT\n{curr_dates_str}",
                "Alert(s)"
            ]
        )

        st.dataframe(
            summary_df,
            use_container_width=True,
            hide_index=True,
            height=min(520, 60 + len(summary_df) * 42)  # Adjust height to show 10 rows comfortably
        )

        # --- Expander under each summary row ---
        st.markdown("### Show Details by Channel & Date")
        for idx, row in merged.iterrows():
            pkg = row['Package']
            expander = st.expander(f"Show More for {pkg}", expanded=False, key=f"expander_{pkg}")
            with expander:
                recent = df[(df['Package'] == pkg) & (df['Date'] >= prev_window_start)]
                if not recent.empty:
                    # Compute channel total revenue for sorting
                    channel_totals = recent.groupby('Channel')['Gross Revenue'].sum().sort_values(ascending=False)
                    for channel in channel_totals.index:
                        channel_df = recent[recent['Channel'] == channel].copy()
                        channel_df = channel_df.sort_values('Date', ascending=False)
                        st.markdown(f"**💰 {channel} (Total: ${int(channel_totals[channel]):,})**")

                        # Prepare display table with icons/colors
                        rows = []
                        prev_rev = None
                        for i, row2 in channel_df.iterrows():
                            date_str = row2['Date'].strftime('%d/%m')
                            # Most recent date: 🟢
                            date_icon = "🟢 " if row2['Date'] == channel_df['Date'].max() else ""
                            # Revenue with arrows
                            curr_rev = row2['Gross Revenue']
                            if prev_rev is not None:
                                if curr_rev > prev_rev:
                                    rev_str = f"**${int(curr_rev):,} ▲**"
                                elif curr_rev < prev_rev:
                                    rev_str = f"**${int(curr_rev):,} ▼**"
                                else:
                                    rev_str = f"${int(curr_rev):,}"
                            else:
                                rev_str = f"**${int(curr_rev):,}**"
                            prev_rev = curr_rev

                            # eCPM
                            ecpm = f"{row2['eCPM']:.2f}"
                            # IVT: icon if >10%
                            ivt_val = row2['IVT (%)'] if 'IVT (%)' in row2 else row2.get('IVT', 0)
                            ivt = f"{int(round(ivt_val))}%"
                            if ivt_val > 10:
                                ivt = f"**{ivt} ⚠️**"
                            # Margin: green/✅ if ≥40, red/❗ if <25
                            margin_val = row2['Margin (%)'] if 'Margin (%)' in row2 else row2.get('Margin', 0)
                            if margin_val >= 40:
                                margin = f"**<span style='color:green'>{int(round(margin_val))}% ✅</span>**"
                            elif margin_val < 25:
                                margin = f"**<span style='color:red'>{int(round(margin_val))}% ❗</span>**"
                            else:
                                margin = f"{int(round(margin_val))}%"
                            # Collect the row
                            rows.append([
                                f"{date_icon}{date_str}",
                                rev_str,
                                ecpm,
                                ivt,
                                margin
                            ])

                        # Build as DataFrame for display
                        disp_df = pd.DataFrame(rows, columns=["Date", "Gross Revenue", "eCPM", "IVT (%)", "Margin (%)"])
                        st.write(disp_df.to_html(escape=False, index=False), unsafe_allow_html=True)
                        st.markdown("---")
                else:
                    st.write("No data available for this package in last 6 days.")

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
