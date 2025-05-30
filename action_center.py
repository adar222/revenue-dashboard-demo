import streamlit as st
import pandas as pd
import numpy as np

def show_action_center_top10(df):
    # Clean/prepare
    df['Date'] = pd.to_datetime(df['Date'])
    df['Gross Revenue'] = pd.to_numeric(df['Gross Revenue'], errors='coerce').fillna(0)
    df['FillRate'] = pd.to_numeric(df['FillRate'], errors='coerce').fillna(0)
    
    # Find latest 6 dates (for 3+3 comparison)
    latest_dates = sorted(df['Date'].unique())[-6:]
    last3 = latest_dates[-3:]
    prev3 = latest_dates[:3]
    
    # Revenue & fill rate for last 3 days and prev 3 days, by package
    last_rev = df[df['Date'].isin(last3)].groupby('Package').agg({
        'Gross Revenue':'sum',
        'FillRate':'mean'
    }).rename(columns={'Gross Revenue':'Last 3d Revenue','FillRate':'Last 3d Fill'})
    
    prev_rev = df[df['Date'].isin(prev3)].groupby('Package').agg({
        'Gross Revenue':'sum',
        'FillRate':'mean'
    }).rename(columns={'Gross Revenue':'Prev 3d Revenue','FillRate':'Prev 3d Fill'})
    
    # Merge and compute trends
    merged = last_rev.merge(prev_rev, left_index=True, right_index=True, how='outer').fillna(0)
    merged['Δ'] = merged['Last 3d Revenue'] - merged['Prev 3d Revenue']
    merged['% Change'] = np.where(
        merged['Prev 3d Revenue']==0, np.nan, merged['Δ']/merged['Prev 3d Revenue']*100
    )
    merged['Fill Δ'] = merged['Last 3d Fill'] - merged['Prev 3d Fill']
    
    # Action recommendation logic
    def action_row(row):
        if row['Δ'] < 0 and abs(row['% Change']) > 30:
            return 'Investigate drop 🚨'
        elif row['Δ'] > 0 and row['% Change'] > 50:
            return 'Scale up! 🚀'
        elif row['Fill Δ'] < -0.05:
            return 'Check fill issues ⚠️'
        else:
            return 'Stable 👍'
    
    merged['Action'] = merged.apply(action_row, axis=1)
    
    # Top 10 packages by absolute revenue change
    top10 = merged.reindex(merged['Δ'].abs().sort_values(ascending=False).index).head(10)
    top10_display = top10.reset_index().rename(columns={'index':'Package'})
    
    # Color formatting for Δ
    def color_delta(val):
        if val > 0:
            return 'background-color: #d4f8e8'  # green
        elif val < 0:
            return 'background-color: #ffe0e0'  # red
        else:
            return ''
    
    st.subheader("Action Center: Top 10 Trending Packages (3d vs Prev 3d)")
    st.caption(f"Latest period: {last3[0].strftime('%Y-%m-%d')} to {last3[-1].strftime('%Y-%m-%d')}")

    st.dataframe(
        top10_display.style.applymap(color_delta, subset=['Δ']),
        use_container_width=True
    )
