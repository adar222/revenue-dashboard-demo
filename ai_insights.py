import pandas as pd
import streamlit as st
# ­­­­FORCE-REDEPLOY

def comma(x):
    return f"{int(x):,}"

def pct(old, new):
    if old == 0:
        return 9999 if new > 0 else 0
    return int(round((new - old) / old * 100))

def show_ai_insights(df):
    # Preprocessing
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    latest_date = df['Date'].max()
    prev_date = df[df['Date'] < latest_date]['Date'].max()

    today_df = df[df['Date'] == latest_date]
    prev_df = df[df['Date'] == prev_date]

    # --- Section 1: Top 10 Apps by Revenue Today ---
    st.subheader(f"Top 10 Packages by Gross Revenue – {latest_date.strftime('%Y-%m-%d')}")
    top_today = today_df.sort_values('Gross Revenue', ascending=False).head(10)
    prev_map = prev_df.set_index('Package')
    
    for i, row in top_today.iterrows():
        pkg = row['Package']
        curr_rev = row['Gross Revenue']
        curr_margin = row['Margin'] if 'Margin' in row else None
        prev = prev_map.loc[pkg] if pkg in prev_map.index else None

        if prev is not None:
            prev_rev = prev['Gross Revenue']
            change = pct(prev_rev, curr_rev)
            prev_fill = prev['FillRate']
            curr_fill = row['FillRate']
            fill_chg = pct(prev_fill, curr_fill)

            prev_ecpm = prev['eCPM']
            curr_ecpm = row['eCPM']
            ecpm_chg = pct(prev_ecpm, curr_ecpm)

            prev_imp = prev['Publisher Impressions']
            curr_imp = row['Publisher Impressions']
            imp_chg = pct(prev_imp, curr_imp)

            # Main driver
            driver_metric = max(
                [('Fill Rate', fill_chg), ('eCPM', ecpm_chg), ('Impressions', imp_chg)],
                key=lambda x: abs(x[1])
            )
            driver_text = f"{driver_metric[0]} {'up' if driver_metric[1]>0 else 'down'} {abs(driver_metric[1])}%"
        else:
            prev_rev = 0
            change = 9999
            driver_text = "No data for previous day"

        # Color for % change
        color = "#22B573" if change > 0 else "#e74c3c"
        sign = "+" if change > 0 else ""

        st.markdown(
            f"**{pkg} ({row['Ad format']})**  \n"
            f"Revenue: <b>${comma(curr_rev)}</b> (Today) | <b>${comma(prev_rev)}</b> (Yesterday)  "
            f"<span style='color:{color};font-weight:bold;'>[{sign}{change}%]</span>  \n"
            f"Margin: {row['Margin']}%  \n"
            f"Main driver: {driver_text}  \n"
            f"eCPM: {comma(prev['eCPM']) if prev is not None else 'N/A'} ➡️ {comma(curr_ecpm)}  \n"
            f"Fill Rate: {int(round(prev['FillRate']*100)) if prev is not None else 'N/A'}% ➡️ {int(round(row['FillRate']*100))}%  \n"
            f"Imps: {comma(prev['Publisher Impressions']) if prev is not None else 'N/A'} ➡️ {comma(curr_imp)}",
            unsafe_allow_html=True
        )
        st.markdown("---")

    # --- Section 2: Packages Dropped from Top 10 ---
    st.subheader(f"Packages Missing from Today's Top 10 (were Top 10 Yesterday) – {latest_date.strftime('%Y-%m-%d')}")
    top10_prev = set(prev_df.sort_values('Gross Revenue', ascending=False)['Package'].head(10))
    top10_today = set(top_today['Package'])
    missing_pkgs = top10_prev - top10_today

    for pkg in missing_pkgs:
        prev_row = prev_df[prev_df['Package'] == pkg].iloc[0]
        curr_rows = today_df[today_df['Package'] == pkg]
        curr_rev = curr_rows.iloc[0]['Gross Revenue'] if not curr_rows.empty else 0
        margin = curr_rows.iloc[0]['Margin'] if not curr_rows.empty else prev_row['Margin']
        change = pct(prev_row['Gross Revenue'], curr_rev)
        prev_fill = prev_row['FillRate']
        curr_fill = curr_rows.iloc[0]['FillRate'] if not curr_rows.empty else 0
        fill_chg = pct(prev_fill, curr_fill)
        prev_ecpm = prev_row['eCPM']
        curr_ecpm = curr_rows.iloc[0]['eCPM'] if not curr_rows.empty else 0
        ecpm_chg = pct(prev_ecpm, curr_ecpm)
        prev_imp = prev_row['Publisher Impressions']
        curr_imp = curr_rows.iloc[0]['Publisher Impressions'] if not curr_rows.empty else 0
        imp_chg = pct(prev_imp, curr_imp)
        driver_metric = max(
            [('Fill Rate', fill_chg), ('eCPM', ecpm_chg), ('Impressions', imp_chg)],
            key=lambda x: abs(x[1])
        )
        driver_text = f"{driver_metric[0]} {'up' if driver_metric[1]>0 else 'down'} {abs(driver_metric[1])}%"

        color = "#e74c3c"
        st.markdown(
            f"**{pkg} ({prev_row['Ad format']})**  \n"
            f"Revenue: <b>${comma(curr_rev)}</b> (Today) | <b>${comma(prev_row['Gross Revenue'])}</b> (Yesterday)  "
            f"<span style='color:{color};font-weight:bold;'>[{change}%]</span>  \n"
            f"Margin: {margin}%  \n"
            f"Main driver: {driver_text}  \n"
            f"eCPM: {comma(prev_ecpm)} ➡️ {comma(curr_ecpm)}  \n"
            f"Fill Rate: {int(round(prev_fill*100))}% ➡️ {int(round(curr_fill*100))}%  \n"
            f"Imps: {comma(prev_imp)} ➡️ {comma(curr_imp)}",
            unsafe_allow_html=True
        )
        st.markdown("---")

