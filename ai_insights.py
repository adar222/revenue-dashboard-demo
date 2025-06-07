import streamlit as st
import pandas as pd

def show_revenue_drop_insight(df, advertiser):
    df = df[df['Advertiser'] == advertiser].copy()
    if df.empty:
        st.info("No data for this advertiser.")
        return
    df['Date'] = pd.to_datetime(df['Date'])
    last_date = df['Date'].max()
    prev_date = last_date - pd.Timedelta(days=1)
    df_last = df[df['Date'] == last_date]
    df_prev = df[df['Date'] == prev_date]
    rev_last = df_last['Gross Revenue'].sum()
    rev_prev = df_prev['Gross Revenue'].sum()
    if rev_prev == 0:
        st.info("Not enough previous day data.")
        return
    pct_drop = 100 * (rev_last - rev_prev) / rev_prev
    st.markdown(f"**Revenue {'dropped' if pct_drop < 0 else 'increased'} {abs(pct_drop):.1f}% (${rev_prev:,.0f} → ${rev_last:,.0f}) vs previous day.**")
    # Find top 3 negative contributors by package
    merged = pd.merge(
        df_last.groupby('Package').agg({'Gross Revenue':'sum','FillRate':'mean','Margin (%)':'mean','IVT (%)':'mean'}).rename(columns=lambda x: x+'_last'),
        df_prev.groupby('Package').agg({'Gross Revenue':'sum','FillRate':'mean','Margin (%)':'mean','IVT (%)':'mean'}).rename(columns=lambda x: x+'_prev'),
        left_index=True, right_index=True, how='outer').fillna(0)
    merged['Rev Δ'] = merged['Gross Revenue_last'] - merged['Gross Revenue_prev']
    merged['Fill Δ'] = merged['FillRate_last'] - merged['FillRate_prev']
    merged['Margin Δ'] = merged['Margin (%)_last'] - merged['Margin (%)_prev']
    merged['IVT Δ'] = merged['IVT (%)_last'] - merged['IVT (%)_prev']
    biggest = merged.sort_values('Rev Δ').head(3)
    for i, (pkg, row) in enumerate(biggest.iterrows(), 1):
        st.markdown(
            f"- 🥇 **{pkg}:** {row['Rev Δ']:+.0f}$, fill rate {row['Fill Δ']:+.1f}%, margin {row['Margin Δ']:+.1f}%, IVT {row['IVT Δ']:+.1f}%"
        )
    st.markdown("**Top Reasons:**")
    st.markdown("1. Lower fill rate on high-revenue packages  \n2. Margin shrinkage  \n3. IVT increased, reducing valid impressions")

def show_ivt_margin_alert(df):
    if df.empty: 
        st.info("No data to show.")
        return
    df['Date'] = pd.to_datetime(df['Date'])
    last_date = df['Date'].max()
    last_day = df[df['Date'] == last_date].copy()
    last_day = last_day[['Package','RPM','IVT (%)','Margin (%)','Alert']]
    show = last_day[(last_day['IVT (%)'] > 10) | (last_day['Margin (%)'] < 20)]
    st.dataframe(show, hide_index=True)

def show_revenue_drop_table(df):
    if df.empty: return
    df['Date'] = pd.to_datetime(df['Date'])
    last_date = df['Date'].max()
    prev_date = last_date - pd.Timedelta(days=1)
    last = df[df['Date']==last_date]
    prev = df[df['Date']==prev_date]
    merged = pd.merge(
        last[['Package','Gross Revenue','Score']],
        prev[['Package','Gross Revenue']].rename(columns={'Gross Revenue':'Prev Gross Revenue'}),
        on='Package', how='inner'
    )
    merged['Δ'] = merged['Gross Revenue'] - merged['Prev Gross Revenue']
    merged['% Drop'] = 100*(merged['Δ']/merged['Prev Gross Revenue'])
    show = merged[(merged['Gross Revenue'] > 50) & (merged['% Drop'] < -20)]
    # Score color
    def score_circle(score):
        if score >= 75:
            return f"{int(score)} 🟢"
        elif score >= 55:
            return f"{int(score)} 🟡"
        else:
            return f"{int(score)} 🔴"
    show['Score'] = show['Score'].apply(score_circle)
    show['Gross Revenue'] = show['Gross Revenue'].map('${:,.0f}'.format)
    show['Prev Gross Revenue'] = show['Prev Gross Revenue'].map('${:,.0f}'.format)
    show['Δ'] = show['Δ'].map('${:,.0f}'.format)
    show['% Drop'] = show['% Drop'].map('{:.0f}%'.format)
    show = show.rename(columns={
        'Gross Revenue':'Last Day Rev',
        'Prev Gross Revenue':'Prev Day Rev'
    })
    st.dataframe(show[['Package','Last Day Rev','Prev Day Rev','Δ','% Drop','Score']], hide_index=True)
