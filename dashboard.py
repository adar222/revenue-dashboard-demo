import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def show_revenue_trends(advertiser):
    # Demo hardcoded data (same for all advertisers for now)
    trend_data = [
        ["easy.sudoku.puzzle.solver.free", 24000, 7000, 17000, 243, "🟩 High ↑"],
        ["com.vottzapps.wordle", 6000, 10000, -4000, -40, "🟥 Drop ↓"],
        ["solitaire.spider.card.free.mania", 2100, 2000, 100, 5, "⬜ Stable"],
        ["in.playsimple.wordtrip", 3800, 5200, -1400, -27, "🟥 Drop ↓"],
        ["paint.by.number.pixel.art.coloring.drawing.puzzle", 8000, 6000, 2000, 33, "🟩 High ↑"],
        ["link.merge.puzzle.onnect.number", 450, 1100, -650, -59, "🟥 Drop ↓"],
        ["sortpuz.water.sort.puzzle.game", 1200, 350, 850, 243, "🟩 High ↑"],
        ["com.goods.master3d.triple.puzzle", 500, 500, 0, 0, "⬜ Stable"],
        ["com.puzzle.fun.free.matching3d", 200, 600, -400, -67, "🟥 Drop ↓"],
        ["radio.israel.fm", 900, 0, 900, 100, "🟩 New/High ↑"]
    ]
    df = pd.DataFrame(trend_data, columns=[
        "Package Name", "Last 3d Revenue", "Prev 3d Revenue", "Δ (Change)", "% Change", "Trend"
    ])

    total_last = df["Last 3d Revenue"].sum()
    total_prev = df["Prev 3d Revenue"].sum()
    total_delta = total_last - total_prev
    total_pct = (total_delta / total_prev) * 100 if total_prev else 0

    # Add summary row
    summary = pd.DataFrame([["TOTAL", total_last, total_prev, total_delta, round(total_pct), ""]], columns=df.columns)
    df = pd.concat([df, summary], ignore_index=True)

    st.subheader(f"Top 10 Trending Packages for {advertiser}")
    st.caption("Last 3d: 2025-05-04 to 2025-05-06 | Prev 3d: 2025-05-01 to 2025-05-03")
    st.dataframe(df, use_container_width=True)

    # Mini bar chart (only for top 10, skip 'TOTAL')
    fig, ax = plt.subplots(figsize=(8, 4))
    bar_width = 0.35
    idx = range(10)
    ax.bar(idx, df["Last 3d Revenue"][:10], bar_width, label='Last 3d', color='mediumseagreen')
    ax.bar([i + bar_width for i in idx], df["Prev 3d Revenue"][:10], bar_width, label='Prev 3d', color='lightcoral')
    ax.set_xticks([i + bar_width/2 for i in idx])
    ax.set_xticklabels(df["Package Name"][:10], rotation=45, ha='right')
    ax.set_ylabel('Revenue')
    ax.set_title('Top 10 Packages – Revenue Comparison')
    ax.legend()
    st.pyplot(fig)
