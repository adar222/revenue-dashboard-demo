import streamlit as st
import pandas as pd

def show_action_center_top10(df):
    # Compute sum revenue for each package for the last 3d and previous 3d
    if 'Date' not in df.columns or 'Package' not in df.columns:
        st.warning("Date or Package column missing.")
        return
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    last_date = df['Date'].max()
    prev3_date = last_date - pd.Timedelta(days=3)
    prev6_date = last_date - pd.Timedelta(days=6)
    # Last 3 days and previous 3 days
    last3 = df[df['Date'] > prev3_date]
    prev3 = df[(df['Date'] <= prev3_date) & (df['Date'] > prev6_date)]
    last3_sum = last3.groupby('Package')['Gross Revenue'].sum()
    prev3_sum = prev3.groupby('Package')['Gross Revenue'].sum()
    joined = pd.DataFrame({'Last 3d Revenue': last3_sum, 'Prev 3d Revenue': prev3_sum})
    joined = joined.fillna(0)
    joined['Δ'] = joined['Last 3d Revenue'] - joined['Prev 3d Revenue']
    joined['% Change'] = joined.apply(lambda x: 0 if x['Prev 3d Revenue']==0 else 100*(x['Δ']/x['Prev 3d Revenue']), axis=1)
    joined = joined.sort_values('Δ', ascending=False).head(10)
    # Add action suggestion
    joined['Action'] = joined['% Change'].apply(lambda x: '✅ Stable' if x > 0 else '🔻 Investigate')
    # Clean display
    joined = joined.reset_index()
    joined['Last 3d Revenue'] = joined['Last 3d Revenue'].map('${:,.0f}'.format)
    joined['Prev 3d Revenue'] = joined['Prev 3d Revenue'].map('${:,.0f}'.format)
    joined['Δ'] = joined['Δ'].map('${:,.0f}'.format)
    joined['% Change'] = joined['% Change'].map('{:.0f}%'.format)
    st.dataframe(joined[['Package', 'Last 3d Revenue', 'Prev 3d Revenue', 'Δ', '% Change', 'Action']], hide_index=True)
