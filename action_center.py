import streamlit as st
import pandas as pd
import numpy as np

def show_action_center_top10(df):
    df['Date'] = pd.to_datetime(df['Date'])
    df['Gross Revenue'] = pd.to_numeric(df['Gross Revenue'], errors='coerce').fillna(0)
    df['FillRate'] = pd.to_numeric(df['FillRate'], errors='coerce').fillna(0)
    if 'Cost' not in df.columns:
        df['Cost'] = 0
    df['Cost'] = pd.to_numeric(df['Cost'], errors='coerce').fillna(0)
    
    latest_dates = sorted(df['Date'].unique())[-6:]
    last3 = latest_dates[-3:]
    prev3 = latest_dates[:3]
    
    last_rev = df[df['Date'].isin(last3)].groupby('Package').agg({
        'Gross Revenue': 'sum',
        'FillRate': 'mean',
        'Cost': 'sum',
    }).rename(columns={'Gross Revenue': 'Last 3d Revenue', 'FillRate': 'Last 3d Fill', 'Cost': 'Last 3d Cost'})
    
    prev_rev = df[df['Date'].isin(prev3)].groupby('Package').agg({
        'Gross Revenue': 'sum',
        'FillRate': 'mean',
        'Cost': 'sum',
    }).rename(columns={'Gross Revenue': 'Prev 3d Revenue', 'FillRate': 'Prev 3d Fill', 'Cost': 'Prev 3d Cost'})
    
    merged = last_rev.merge(prev_rev, left_index=True, right_index=True, how='outer').fillna(0)
    merged['Δ'] = merged['Last 3d Revenue'] - merged['Prev 3d Revenue']
    merged['% Change'] = np.where(
        merged['Prev 3d Revenue'] == 0, np.nan, merged['Δ'] / merged['Prev 3d Revenue'] * 100
    )
    merged['Fill Δ'] = merged['Last 3d Fill'] - merged['Prev 3d Fill']
    merged['Last 3d Margin %'] = np.where(
        merged['Last 3d Revenue'] == 0,
        np.nan,
        100 * (merged['Last 3d Revenue'] - merged['Last 3d Cost']) / merged['Last 3d Revenue']
    )
    merged['Margin Alert'] = merged['Last 3d Margin %'] < 25

    def action_row(row):
        if row['Margin Alert']:
            return 'Margin drop! 🔻'
        if row['Δ'] < 0 and abs(row['% Change']) > 30:
            return 'Investigate drop 🚨'
        elif row['Δ'] > 0 and row['% Change'] > 50:
            return 'Scale up! 🚀'
        elif row['Fill Δ'] < -0.05:
            return 'Check fill issues ⚠️'
        else:
            return 'Stable 👍'
    merged['Action'] = merged.apply(action_row, axis=1)
    
    top10 = merged.reindex(merged['Δ'].abs().sort_values(ascending=False).index).head(10)
    top10_display = top10.reset_index().rename(columns={'index': 'Package'})

    # Make sure these columns exist for display and alert
    top10_display['Last 3d Cost'] = top10['Last 3d Cost'].values
    top10_display['Margin Alert'] = top10['Margin Alert'].values

    def fmt_money(x):
        return f"${int(round(x)):,}" if pd.notnull(x) else ""
    def fmt_pct(x):
        return f"{int(round(x)):+d}%" if pd.notnull(x) else ""
    def fmt_fill(x):
        return f"{x:.0%}" if pd.notnull(x) else ""
    def fmt_margin(x):
        return f"{x:.1f}%" if pd.notnull(x) else ""
    
    top10_display['Last 3d Revenue'] = top10_display['Last 3d Revenue'].apply(fmt_money)
    top10_display['Prev 3d Revenue'] = top10_display['Prev 3d Revenue'].apply(fmt_money)
    top10_display['Δ'] = top10_display['Δ'].apply(fmt_money)
    top10_display['% Change'] = top10_display['% Change'].apply(fmt_pct)
    top10_display['Last 3d Fill'] = top10_display['Last 3d Fill'].apply(fmt_fill)
    top10_display['Prev 3d Fill'] = top10_display['Prev 3d Fill'].apply(fmt_fill)
    top10_display['Fill Δ'] = top10_display['Fill Δ'].apply(lambda x: fmt_pct(x * 100))
    top10_display['Last 3d Margin %'] = top10_display['Last 3d Margin %'].apply(fmt_margin)
    
    st.subheader("Action Center: Top 10 Trending Packages (3d vs Prev 3d)")
    st.caption(f"Latest period: {last3[0].strftime('%Y-%m-%d')} to {last3[-1].strftime('%Y-%m-%d')}")

    def highlight_row(row):
        if row['Margin Alert']:
            return ['background-color: #FFCDD2'] * len(row)
        else:
            return [''] * len(row)

    st.dataframe(top10_display.style.apply(highlight_row, axis=1), use_container_width=True)

    # --- Show alert and table if margin alert present ---
    alert_rows = top10_display[top10_display['Margin Alert']]
    if not alert_rows.empty:
        st.warning("⚠️ Margin below 25% detected on these packages:", icon="⚠️")
        st.dataframe(alert_rows[['Package', 'Last 3d Revenue', 'Last 3d Cost', 'Last 3d Margin %', 'Action']], use_container_width=True)
