import pandas as pd
import streamlit as st

def show_ai_insights(df):
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')

    latest_date = df['Date'].max()
    previous_date = df[df['Date'] < latest_date]['Date'].max()

    # Only keep packages that appear in BOTH dates
    packages_latest = set(df[df['Date'] == latest_date]['Package'])
    packages_prev = set(df[df['Date'] == previous_date]['Package'])
    valid_packages = packages_latest & packages_prev

    if not valid_packages:
        st.warning("No packages found with data for both the latest and previous dates.")
        return

    # Compute % revenue change for all valid packages
    movers = []
    for pkg in valid_packages:
        curr_row = df[(df['Date'] == latest_date) & (df['Package'] == pkg)].iloc[0]
        prev_row = df[(df['Date'] == previous_date) & (df['Package'] == pkg)].iloc[0]
        prev_rev = prev_row['Gross Revenue']
        curr_rev = curr_row['Gross Revenue']
        if prev_rev != 0:
            pct_change = ((curr_rev - prev_rev) / prev_rev) * 100
        else:
            pct_change = float('inf')
        movers.append({
            'Package': pkg,
            'Ad format': curr_row['Ad format'],
            'Previous Revenue': prev_rev,
            'Current Revenue': curr_rev,
            'Change (%)': pct_change,
            'Previous eCPM': prev_row['eCPM'],
            'Current eCPM': curr_row['eCPM'],
            'Previous FillRate': prev_row['FillRate'],
            'Current FillRate': curr_row['FillRate'],
            'Previous Date': previous_date,
            'Current Date': latest_date,
        })

    # Convert to DataFrame and sort
    movers_df = pd.DataFrame(movers)
    top_movers = movers_df.sort_values('Change (%)', ascending=False).head(8)
    bottom_movers = movers_df.sort_values('Change (%)', ascending=True).head(8)

    st.header("🤖 AI Insights: Top 8 Revenue Increases (Biggest Movers)")
    for _, row in top_movers.iterrows():
        st.markdown(
            f"""
            <span style="color:#22B573;font-size:18px;"><b>⬆️ {row['Package']} ({row['Ad format']})</b></span>  
            <span style="font-size:15px;">
            {row['Current Date'].strftime('%Y-%m-%d')}: Gross Revenue changed by <b>{row['Change (%)']:.1f}%</b>
            (from <b>${row['Previous Revenue']:.2f}</b> to <b>${row['Current Revenue']:.2f}</b>)
            </span>
            """, unsafe_allow_html=True)
        st.write(f"eCPM: ${row['Previous eCPM']:.2f} ➡️ ${row['Current eCPM']:.2f}")
        st.write(f"Fill Rate: {row['Previous FillRate']:.2%} ➡️ {row['Current FillRate']:.2%}")
        st.markdown("---")

    st.header("🤖 AI Insights: Top 8 Revenue Decreases (Biggest Drops)")
    for _, row in bottom_movers.iterrows():
        st.markdown(
            f"""
            <span style="color:#e74c3c;font-size:18px;"><b>⬇️ {row['Package']} ({row['Ad format']})</b></span>  
            <span style="font-size:15px;">
            {row['Current Date'].strftime('%Y-%m-%d')}: Gross Revenue changed by <b>{row['Change (%)']:.1f}%</b>
            (from <b>${row['Previous Revenue']:.2f}</b> to <b>${row['Current Revenue']:.2f}</b>)
            </span>
            """, unsafe_allow_html=True)
        st.write(f"eCPM: ${row['Previous eCPM']:.2f} ➡️ ${row['Current eCPM']:.2f}")
        st.write(f"Fill Rate: {row['Previous FillRate']:.2%} ➡️ {row['Current FillRate']:.2%}")
        st.markdown("---")
