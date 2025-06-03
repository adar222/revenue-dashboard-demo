import pandas as pd
import streamlit as st

def comma(x):
    return f"{int(x):,}"

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

    movers = []
    for pkg in valid_packages:
        curr_df = df[(df['Date'] == latest_date) & (df['Package'] == pkg)]
        prev_df = df[(df['Date'] == previous_date) & (df['Package'] == pkg)]
        # Defensive: skip if either is missing
        if curr_df.empty or prev_df.empty:
            continue
        curr_row = df[(df['Date'] == latest_date) & (df['Package'] == pkg)].iloc[0]
        prev_row = prev_df.iloc[0]
        prev_rev = prev_row['Gross Revenue']
        curr_rev = curr_row['Gross Revenue']
        if prev_rev != 0:
            pct_change = int(round((curr_rev - prev_rev) / prev_rev * 100))
        else:
            pct_change = 9999  # Big number for infinite jump

        # Calculate changes for main driver analysis
        prev_fill = prev_row['FillRate']
        curr_fill = curr_row['FillRate']
        fill_change = int(round((curr_fill - prev_fill) / prev_fill * 100)) if prev_fill != 0 else 0

        prev_ecpm = prev_row['eCPM']
        curr_ecpm = curr_row['eCPM']
        ecpm_change = int(round((curr_ecpm - prev_ecpm) / prev_ecpm * 100)) if prev_ecpm != 0 else 0

        prev_imp = prev_row['Publisher Impressions']
        curr_imp = curr_row['Publisher Impressions']
        imp_change = int(round((curr_imp - prev_imp) / prev_imp * 100)) if prev_imp != 0 else 0

        # Determine main driver (largest absolute change)
        driver_metric = max(
            [('Fill Rate', fill_change), ('eCPM', ecpm_change), ('Impressions', imp_change)],
            key=lambda x: abs(x[1])
        )
        driver_text = f"{driver_metric[0].lower()} {'up' if driver_metric[1]>0 else 'down'} {abs(driver_metric[1])}%"

        movers.append({
            'Package': pkg,
            'Ad format': curr_row['Ad format'],
            'Previous Revenue': comma(prev_rev),
            'Current Revenue': comma(curr_rev),
            'Change (%)': pct_change,
            'Previous eCPM': comma(prev_ecpm),
            'Current eCPM': comma(curr_ecpm),
            'Previous FillRate': int(round(prev_fill * 100)),
            'Current FillRate': int(round(curr_fill * 100)),
            'Previous Imps': comma(prev_imp),
            'Current Imps': comma(curr_imp),
            'Previous Date': previous_date,
            'Current Date': latest_date,
            'Main Driver': driver_text
        })


    # Sort and pick top/bottom 5
    movers_df = pd.DataFrame(movers)
    top5 = movers_df.sort_values('Change (%)', ascending=False).head(5)
    bottom5 = movers_df.sort_values('Change (%)', ascending=True).head(5)

    # --- Top 5 Movers Up ---
    st.subheader("Top 5 Movers Up")
    for _, row in top5.iterrows():
        st.markdown(
            f"⬆️ **{row['Package']} ({row['Ad format']})**  \n"
            f"{row['Current Date'].strftime('%Y-%m-%d')}: Revenue +{row['Change (%)']}% (from {row['Previous Revenue']} to {row['Current Revenue']})  \n"
            f"**Main driver:** {row['Main Driver']}"
        )
        st.markdown(
            f"eCPM: {row['Previous eCPM']} ➡️ {row['Current eCPM']}  \n"
            f"Fill Rate: {row['Previous FillRate']}% ➡️ {row['Current FillRate']}%  \n"
            f"Publisher Imps: {row['Previous Imps']} ➡️ {row['Current Imps']}"
        )
        st.markdown("---")

    # --- Top 5 Movers Down ---
    st.subheader("Top 5 Movers Down")
    for _, row in bottom5.iterrows():
        st.markdown(
            f"⬇️ **{row['Package']} ({row['Ad format']})**  \n"
            f"{row['Current Date'].strftime('%Y-%m-%d')}: Revenue {row['Change (%)']}% (from {row['Previous Revenue']} to {row['Current Revenue']})  \n"
            f"**Main driver:** {row['Main Driver']}"
        )
        st.markdown(
            f"eCPM: {row['Previous eCPM']} ➡️ {row['Current eCPM']}  \n"
            f"Fill Rate: {row['Previous FillRate']}% ➡️ {row['Current FillRate']}%  \n"
            f"Publisher Imps: {row['Previous Imps']} ➡️ {row['Current Imps']}"
        )
        st.markdown("---")

    # --- Actionable Opportunities ---
    new_top10 = []
    opportunity = []
    recent = set(top5['Package']).union(set(bottom5['Package']))
    all_top_latest = set(df[df['Date'] == latest_date].sort_values('Gross Revenue', ascending=False)['Package'].head(10))
    all_top_prev = set(df[df['Date'] == previous_date].sort_values('Gross Revenue', ascending=False)['Package'].head(10))
    for pkg in all_top_latest - all_top_prev:
        new_top10.append(pkg)
    for _, row in movers_df.iterrows():
        if row['Current FillRate'] > 90 and int(row['Current eCPM'].replace(',', '')) < 2:
            opportunity.append(row['Package'])

    st.subheader("Actionable")
    if new_top10:
        for pkg in new_top10:
            st.markdown(f"- **{pkg}** entered the top 10. Monitor performance.")
    if opportunity:
        for pkg in set(opportunity) - recent:
            st.markdown(f"- **{pkg}**: high fill rate, low eCPM—suggest floor review.")
    if not new_top10 and not opportunity:
        st.markdown("No new actionable insights today.")

    # --- Top 10 Revenue Apps Impact ---
    st.subheader("Top 10 Apps by Gross Revenue – Impact")

    top10_revenue = df[df['Date'] == latest_date].sort_values('Gross Revenue', ascending=False).head(10)
    for idx, row in top10_revenue.iterrows():
        pkg = row['Package']
        curr_rev = row['Gross Revenue']
        prev_rows = df[(df['Date'] == previous_date) & (df['Package'] == pkg)]
        if not prev_rows.empty:
            prev_rev = prev_rows.iloc[0]['Gross Revenue']
            change = int(round((curr_rev - prev_rev) / prev_rev * 100)) if prev_rev != 0 else 9999
            # Main driver logic (reuse from previous)
            prev_imp = prev_rows.iloc[0]['Publisher Impressions']
            curr_imp = row['Publisher Impressions']
            imp_change = int(round((curr_imp - prev_imp) / prev_imp * 100)) if prev_imp != 0 else 0
            prev_ecpm = prev_rows.iloc[0]['eCPM']
            curr_ecpm = row['eCPM']
            ecpm_change = int(round((curr_ecpm - prev_ecpm) / prev_ecpm * 100)) if prev_ecpm != 0 else 0
            prev_fill = prev_rows.iloc[0]['FillRate']
            curr_fill = row['FillRate']
            fill_change = int(round((curr_fill - prev_fill) / prev_fill * 100)) if prev_fill != 0 else 0

            driver_metric = max(
                [('Fill Rate', fill_change), ('eCPM', ecpm_change), ('Impressions', imp_change)],
                key=lambda x: abs(x[1])
            )
            driver_text = f"{driver_metric[0].lower()} {'up' if driver_metric[1]>0 else 'down'} {abs(driver_metric[1])}%"

            # Color for up/down
            color = "#22B573" if change > 0 else "#e74c3c"
            sign = "+" if change > 0 else ""

            st.markdown(
                f"**{idx+1}. {pkg} ({row['Ad format']})**  \n"
                f"Date: {latest_date.strftime('%Y-%m-%d')}  \n"
                f"Revenue: <b>${int(curr_rev):,}</b> <i>(Current)</i> | <b>${int(prev_rev):,}</b> <i>(Previous)</i>  "
                f"<span style='color:{color};font-weight:bold;'>[{sign}{change}%]</span>  \n"
                f"Main driver: {driver_text}",
                unsafe_allow_html=True
            )
            st.markdown("---")
        else:
            st.markdown(f"**{pkg} ({row['Ad format']})**  \nNo data for previous day.")
            st.markdown("---")
