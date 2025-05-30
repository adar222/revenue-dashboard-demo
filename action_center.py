import streamlit as st
import pandas as pd
import numpy as np

def show_action_center_top10(df):
    # Convert types and clean up
    df['Date'] = pd.to_datetime(df['Date'])
    df['Gross Revenue'] = pd.to_numeric(df['Gross Revenue'], errors='coerce').fillna(0)
    df['FillRate'] = pd.to_numeric(df['FillRate'], errors='coerce').fillna(0)
    if 'Margin' in df.columns:
        df['Margin'] = pd.to_numeric(df['Margin'], errors='coerce').fillna(0)
    
    # Find latest 6 dates (for 3+3 comparison)
    latest_dates = sorted(df['Date'].unique())[-6:]
    last3 = latest_dates[-3:]
    prev3 = latest_dates[:3]
    
    # Revenue & fill rate for last 3 days and prev 3 days, by package
    last_rev = df[df['Date'].isin(last3)].groupby('Package').agg({
        'Gross Revenue':'sum',
        'FillRate':'mean',
        'Margin': 'mean' if 'Margin' in df.columns else 'first'
    }).rename(columns={'Gross Revenue':'Last 3d Revenue','FillRate':'Last 3d Fill','Margin': 'Last 3d Margin'})
    
    prev_rev = df[df['Date'].isin(prev3)].groupby('Package').agg({
        'Gross Revenue':'sum',
        'FillRate':'mean',
        'Margin': 'mean' if 'Margin' in df.columns else 'first'
    }).rename(columns={'Gross Revenue':'Prev 3d Revenue','FillRate':'Prev 3d Fill','Margin': 'Prev 3d Margin'})
    
    # Merge and compute trends
    merged = last_rev.merge(prev_rev, left_index=True, right_index=True, how='outer').fillna(0)
    merged['Δ'] = merged['Last 3d Revenue'] - merged['Prev 3d Revenue']
    merged['% Change'] = np.where(
        merged['Prev 3d Revenue']==0, np.nan, merged['Δ']/merged['Prev 3d Revenue']*100
    )
    merged['Fill Δ'] = merged['Last 3d Fill'] - merged['Prev 3d Fill']
    
    # Action recommendation logic
    def action_row(row):
        msg = []
        if row['Δ'] < 0 and abs(row['% Change']) > 30:
            msg.append('Investigate drop 🚨')
        elif row['Δ'] > 0 and row['% Change'] > 50:
            msg.append('Scale up! 🚀')
        elif row['Fill Δ'] < -0.05:
            msg.append('Check fill issues ⚠️')
        else:
            msg.append('Stable 👍')
        # Margin alert
        try:
            if float(row['Last 3d Margin']) < 0.25:
                msg.append('Low margin ⚠️')
        except Exception:
            pass
        return " | ".join(msg)
    merged['Action'] = merged.apply(action_row, axis=1)
    
    # Top 10 by absolute revenue change
    top10 = merged.reindex(merged['Δ'].abs().sort_values(ascending=False).index).head(10)
    top10_display = top10.reset_index().rename(columns={'index':'Package'})
    
    # Inline row highlight for margin (do BEFORE formatting to strings)
    def highlight_margin(row):
        try:
            if float(row['Last 3d Margin']) < 0.25:
                return ['background-color: #fff3cd'] * len(row)
        except Exception:
            pass
        return [''] * len(row)
    
    styled_df = top10_display.style.apply(highlight_margin, axis=1)
    
    # NOW do formatting for display
    def fmt_money(x):
        return f"${int(round(x)):,}" if pd.notnull(x) else ""
    def fmt_pct(x):
        return f"{int(round(x)):+d}%" if pd.notnull(x) else ""
    def fmt_fill(x):
        return f"{x:.0%}" if pd.notnull(x) else ""
    def fmt_margin(x):
        return f"{x:.0%}" if pd.notnull(x) else ""
    
    for col in ['Last 3d Revenue', 'Prev 3d Revenue', 'Δ']:
        if col in top10_display:
            top10_display[col] = top10_display[col].apply(fmt_money)
    if '% Change' in top10_display:
        top10_display['% Change'] = top10_display['% Change'].apply(fmt_pct)
    for col in ['Last 3d Fill', 'Prev 3d Fill']:
        if col in top10_display:
            top10_display[col] = top10_display[col].apply(fmt_fill)
    if 'Fill Δ' in top10_display:
        top10_display['Fill Δ'] = top10_display['Fill Δ'].apply(lambda x: fmt_pct(x*100))
    if 'Last 3d Margin' in top10_display:
        top10_display['Last 3d Margin'] = top10_display['Last 3d Margin'].apply(fmt_margin)
    if 'Prev 3d Margin' in top10_display:
        top10_display['Prev 3d Margin'] = top10_display['Prev 3d Margin'].apply(fmt_margin)
    
    st.subheader("Action Center: Top 10 Trending Packages (3d vs Prev 3d)")
    st.caption(f"Latest period: {last3[0].strftime('%Y-%m-%d')} to {last3[-1].strftime('%Y-%m-%d')}")
    st.dataframe(styled_df, use_container_width=True)

def show_dropped_channels(df):
    # Find channels with a drop >80% in publisher impressions from prev 3d to last 3d
    df['Date'] = pd.to_datetime(df['Date'])
    df['Publisher Impressions'] = pd.to_numeric(df['Publisher Impressions'], errors='coerce').fillna(0)
    latest_dates = sorted(df['Date'].unique())[-6:]
    last3 = latest_dates[-3:]
    prev3 = latest_dates[:3]
    last_by_channel = df[df['Date'].isin(last3)].groupby('Channel')['Publisher Impressions'].sum()
    prev_by_channel = df[df['Date'].isin(prev3)].groupby('Channel')['Publisher Impressions'].sum()
    channel_df = pd.DataFrame({'Last 3d': last_by_channel, 'Prev 3d': prev_by_channel}).fillna(0)
    channel_df['% Drop'] = np.where(channel_df['Prev 3d']==0, np.nan, 100*(channel_df['Prev 3d']-channel_df['Last 3d'])/channel_df['Prev 3d'])
    # Only channels with at least some impressions before
    dropped = channel_df[channel_df['% Drop'] > 80]
    if not dropped.empty:
        st.error("⚠️ Critical: The following channels dropped >80% in impressions (check connectivity/settings):")
        st.dataframe(dropped.reset_index()[['Channel','Prev 3d','Last 3d','% Drop']], use_container_width=True)

def show_best_worst_formats(df):
    # Find top/bottom ad formats by revenue in last 3d
    df['Date'] = pd.to_datetime(df['Date'])
    df['Gross Revenue'] = pd.to_numeric(df['Gross Revenue'], errors='coerce').fillna(0)
    latest_dates = sorted(df['Date'].unique())[-3:]
    recent = df[df['Date'].isin(latest_dates)]
    by_fmt = recent.groupby('Ad format')['Gross Revenue'].sum().sort_values(ascending=False)
    if not by_fmt.empty:
        st.info(f"💡 Top ad format (last 3d): **{by_fmt.index[0]}** (${int(round(by_fmt.iloc[0])):,})")
        if len(by_fmt) > 1:
            st.warning(f"Low performer: **{by_fmt.index[-1]}** (${int(round(by_fmt.iloc[-1])):,})")
