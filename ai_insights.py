import pandas as pd
import streamlit as st

def to_number(x):
    """Remove $ and commas, convert to float, or 0 if not possible."""
    try:
        if isinstance(x, str):
            x = x.replace('$', '').replace(',', '').strip()
        return float(x)
    except Exception:
        return 0

def pct(new, old):
    try:
        if old == 0:
            return 9999
        return int(round((new - old) / old * 100))
    except Exception:
        return 0

def show_ai_insights(df):
    # --- Convert columns to appropriate types ---
    df['Date'] = pd.to_datetime(df['Date'])
    for col in ['Gross Revenue', 'Revenue cost', 'eCPM']:
        df[col] = df[col].apply(to_number)
    df['FillRate'] = df['FillRate'].astype(str).str.replace('%', '').astype(float)
    df['FillRate'] = df['FillRate'] / 100

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

    movers = []
    for pkg in valid_packages:
        curr_df = df[(df['Date'] == latest_date) & (df['Package'] == pkg)]
        prev_df = df[(df['Date'] == previous_date) & (df['Package'] == pkg)]
        if curr_df.empty or prev_df.empty:
            continue
        curr_row = curr_df.iloc[0]
        prev_row = prev_df.iloc[0]

        prev_rev = prev_row['Gross Revenue']
        curr_rev = curr_row['Gross Revenue']
        prev_cost = prev_row['Revenue cost']
        curr_cost = curr_row['Revenue cost']

        prev_margin = ((prev_rev - prev_cost) / prev_rev * 100) if prev_rev != 0 else 0
        curr_margin = ((curr_rev - curr_cost) / curr_rev * 100) if curr_rev != 0 else 0

        prev_fill = prev_row['FillRate']
        curr_fill = curr_row['FillRate']
        fill_change = pct(curr_fill, prev_fill)

        prev_ecpm = prev_row['eCPM']
        curr_ecpm = curr_row['eCPM']
        ecpm_change = pct(curr_ecpm, prev_ecpm)

        prev_imp = to_number(prev_row['Publisher Impressions'])
        curr_imp = to_number(curr_row['Publisher Impressions'])
        imp_change = pct(curr_imp, prev_imp)

        driver_metric = max(
            [('Fill Rate', fill_change), ('eCPM', ecpm_change), ('Impressions', imp_change)],
            key=lambda x: abs(x[1])
        )
        driver_text = f"{driver_metric[0].lower()} {'up' if driver_metric[1]>0 else 'down'} {abs(driver_metric[1])}%"

        movers.append({
            'Package': pkg,
            'Ad format': curr_row['Ad format'],
            'Previous Revenue': prev_rev,
            'Current Revenue': curr_rev,
            'Change (%)': pct(curr_rev, prev_rev),
            'Previous eCPM': prev_ecpm,
            'Current eCPM': curr_ecpm,
            'Previous FillRate': prev_fill,
            'Current FillRate': curr_fill,
            'Previous Imps': prev_imp,
            'Current Imps': curr_imp,
            'Previous Margin': prev_margin,
            'Current Margin': curr_margin,
            'Main Driver': driver_text
        })

    # Top 10 by current day revenue
    movers_df = pd.DataFrame(movers)
    movers_df = movers_df.sort_values('Current Revenue', ascending=False).head(10)

    st.subheader(f"Top 10 Packages by Gross Revenue – {latest_date.strftime('%Y-%m-%d')}")
    for _, row in movers_df.iterrows():
        change = row['Change (%)']
        sign = "+" if change > 0 else ""
        color = "#22B573" if change > 0 else "#e74c3c"
        st.markdown(
            f"**{row['Package']} ({row['Ad format']})**  \n"
            f"Revenue: <b>{int(row['Current Revenue']):,}</b> (<i>Today</i>) | <b>{int(row['Previous Revenue']):,}</b> (Yesterday) "
            f"<span style='color:{color};font-weight:bold;'>[{sign}{change}%]</span>  \n"
            f"Margin: <b>{row['Current Margin']:.1f}%</b> (Today) | <b>{row['Previous Margin']:.1f}%</b> (Yesterday)  \n"
            f"Main driver: {row['Main Driver']}  \n"
            f"eCPM: {row['Previous eCPM']} ➡️ {row['Current eCPM']}  \n"
            f"Fill Rate: {row['Previous FillRate']*100:.1f}% ➡️ {row['Current FillRate']*100:.1f}%  \n"
            f"Imps: {int(row['Previous Imps']):,} ➡️ {int(row['Current Imps']):,}",
            unsafe_allow_html=True
        )
        st.markdown("---")
