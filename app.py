import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import openai

st.set_page_config(page_title="Revenue Insight Dashboard", layout="wide")

if "OPENAI_API_KEY" not in st.secrets:
    openai.api_key = st.text_input(
        "Enter your OpenAI API key:",
        type="password",
        help="You can also set OPENAI_API_KEY as an environment variable."
    )
else:
    openai.api_key = st.secrets["OPENAI_API_KEY"]

st.sidebar.title("🔧 Dashboard Settings")
uploaded_file = st.sidebar.file_uploader(
    "Upload your revenue Excel file:",
    type=["xlsx", "xls"]
)

if uploaded_file is None:
    st.sidebar.info("Upload an Excel file to get started.")
    st.write("📂 Please upload an Excel file on the left to load data.")
    st.stop()

@st.cache_data
def load_data(excel_bytes):
    # Explicitly map your actual Excel headers to the expected dashboard fields
    col_map = {
        "Product": "Product",
        "Date": "Date",
        "Advertiser": "Advertiser",
        "GrossRevenue": "GrossRevenue",
        "Cost": "Cost",
        "PublisherImpressions": "PublisherImpressions",
        "AdvImpressionsClean": "AdvImpressionsClean",
        "IVTRate": "IVTRate",
        "RPM": "RPM"
    }
    df = pd.read_excel(excel_bytes)
    # Keep and rename only the required columns for dashboard logic
    required_cols = list(col_map.keys())
    for col in required_cols:
        if col not in df.columns:
            raise KeyError(f"Column '{col}' not found in the uploaded file.")
    df = df[required_cols]
    df.rename(columns=col_map, inplace=True)
    # Data type conversions
    df["Date"] = pd.to_datetime(df["Date"])
    for num_col in ["GrossRevenue", "Cost", "PublisherImpressions", "AdvImpressionsClean", "IVTRate", "RPM"]:
        df[num_col] = pd.to_numeric(df[num_col], errors="coerce").fillna(0)
    df["Discrepancy"] = df["PublisherImpressions"] - df["AdvImpressionsClean"]
    df["Margin"] = np.where(
        df["GrossRevenue"] > 0,
        (df["GrossRevenue"] - df["Cost"]) / df["GrossRevenue"],
        0
    )
    return df

try:
    df = load_data(uploaded_file)
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.write("Excel columns found:", pd.read_excel(uploaded_file, nrows=0).columns.tolist())
    st.stop()

min_date = df["Date"].min().date()
max_date = df["Date"].max().date()
date_range = st.sidebar.date_input(
    "Date range:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)
if len(date_range) != 2:
    st.error("Select a valid start and end date.")
    st.stop()
start_date, end_date = date_range

all_advertisers = df["Advertiser"].unique().tolist()
selected_advertisers = st.sidebar.multiselect(
    "Select advertiser(s):",
    options=all_advertisers,
    default=all_advertisers
)

mask = (
    (df["Date"].dt.date >= start_date)
    & (df["Date"].dt.date <= end_date)
    & (df["Advertiser"].isin(selected_advertisers))
)
df_filtered = df.loc[mask].copy()
if df_filtered.empty:
    st.warning("No data matches the selected filters.")
else:
    st.success(f"Loaded {len(df_filtered):,} rows after filtering.")

st.title("📊 Revenue Insight Dashboard")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Revenue Trends", "Discrepancy Monitor", "IVT Insights", "Margin Alerts", "Product Optimization"]
)

with tab1:
    st.header("📈 Revenue Trends")
    if df_filtered.empty:
        st.info("No data for Revenue Trends.")
    else:
        rev_ts = (
            df_filtered.groupby("Date")["GrossRevenue"]
            .sum()
            .reset_index()
            .sort_values("Date")
        )
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.plot(rev_ts["Date"], rev_ts["GrossRevenue"], marker="o")
        ax.set_xlabel("Date")
        ax.set_ylabel("Total Gross Revenue")
        ax.set_title("Total Gross Revenue over Time")
        ax.grid(True)
        st.pyplot(fig)

        if len(selected_advertisers) > 1:
            by_adv = (
                df_filtered.groupby(["Date", "Advertiser"])["GrossRevenue"]
                .sum()
                .unstack(fill_value=0)
            )
            fig2, ax2 = plt.subplots(figsize=(8, 3))
            for adv in by_adv.columns:
                ax2.plot(by_adv.index, by_adv[adv], label=adv)
            ax2.set_xlabel("Date")
            ax2.set_ylabel("Gross Revenue")
            ax2.set_title("Gross Revenue by Advertiser")
            ax2.legend()
            ax2.grid(True)
            st.pyplot(fig2)

with tab2:
    st.header("⚖️ Discrepancy Monitor")
    if df_filtered.empty:
        st.info("No data for Discrepancy Monitor.")
    else:
        top_n = st.slider(
            "Show top N products by highest absolute discrepancy:",
            min_value=5, max_value=50, value=10, step=5
        )
        disc_df = (
            df_filtered.groupby("Product")["Discrepancy"]
            .sum()
            .abs()
            .reset_index()
            .rename(columns={"Discrepancy": "TotalAbsDiscrepancy"})
            .sort_values("TotalAbsDiscrepancy", ascending=False)
            .head(top_n)
        )
        st.markdown(f"#### Top {top_n} Products by |Discrepancy|")
        st.dataframe(disc_df, use_container_width=True)

        st.markdown("#### Inspect Individual Product")
        product_select = st.selectbox(
            "Select a product to see PubImpressions vs AdvImpressionsClean over time:",
            options=df_filtered["Product"].unique().tolist()
        )
        pkg_df = df_filtered[df_filtered["Product"] == product_select]
        if not pkg_df.empty:
            ts = (
                pkg_df.groupby("Date")[["PublisherImpressions", "AdvImpressionsClean"]]
                .sum()
                .reset_index()
                .sort_values("Date")
            )
            fig3, ax3 = plt.subplots(figsize=(8, 3))
            ax3.plot(ts["Date"], ts["PublisherImpressions"], marker="o", label="PubImpr")
            ax3.plot(ts["Date"], ts["AdvImpressionsClean"], marker="o", label="AdvClean")
            ax3.set_xlabel("Date")
            ax3.set_ylabel("Impressions")
            ax3.set_title(f"Impressions over Time for {product_select}")
            ax3.legend()
            ax3.grid(True)
            st.pyplot(fig3)
        else:
            st.info("No data for the selected product.")

with tab3:
    st.header("🚨 IVT (Invalid Traffic) Insights")
    if df_filtered.empty:
        st.info("No data for IVT Insights.")
    else:
        ivt_ts = (
            df_filtered.groupby("Date")["IVTRate"]
            .mean()
            .reset_index()
            .sort_values("Date")
        )
        fig4, ax4 = plt.subplots(figsize=(8, 3))
        ax4.plot(ivt_ts["Date"], ivt_ts["IVTRate"], marker="o")
        ax4.set_xlabel("Date")
        ax4.set_ylabel("Avg IVT Rate")
        ax4.set_title("Average IVT Rate over Time")
        ax4.grid(True)
        st.pyplot(fig4)

        overall_mean = df_filtered["IVTRate"].mean()
        overall_std = df_filtered["IVTRate"].std()
        threshold = overall_mean + 2 * overall_std
        st.markdown(f"**Spike threshold (mean + 2·std):** {threshold:.2f}")
        spikes = df_filtered[df_filtered["IVTRate"] > threshold]
        if not spikes.empty:
            st.markdown("### Detected IVT Spikes")
            st.dataframe(
                spikes[["Date", "Product", "Advertiser", "IVTRate"]]
                .sort_values("IVTRate", ascending=False),
                use_container_width=True
            )
        else:
            st.success("No IVT spikes detected in the selected period.")

with tab4:
    st.header("🚦 Margin Alerts (Margin < 25%)")
    if df_filtered.empty:
        st.info("No data for Margin Alerts.")
    else:
        low_margin_df = df_filtered[df_filtered["Margin"] < 0.25]
        if not low_margin_df.empty:
            summary = (
                low_margin_df.groupby("Product")["Margin"]
                .mean()
                .reset_index()
                .rename(columns={"Margin": "AvgMargin"})
                .sort_values("AvgMargin")
            )
            st.markdown(f"#### {len(summary):,} product(s) below 25% margin")
            st.dataframe(summary, use_container_width=True)
        else:
            st.success("No products below 25% margin in the selected period.")

with tab5:
    st.header("🛠️ Product Optimization Tool (Demo)")
    st.markdown(
        """
        Blocks any product where:
        - RPM ≤ 0.001 **and**
        - GrossRevenue ≤ $1 (or blank)

        Output is grouped by Product with RPM, GrossRevenue.
        """
    )
    if df_filtered.empty:
        st.info("No data for Product Optimization Tool.")
    else:
        if st.button("Run Optimization"):
            opt_df = df_filtered[
                (df_filtered["RPM"] <= 0.001) &
                ((df_filtered["GrossRevenue"] <= 1) | (df_filtered["GrossRevenue"].isna()))
            ].copy()
            if opt_df.empty:
                st.success("No products meet block criteria.")
            else:
                out = (
                    opt_df[["Product", "RPM", "GrossRevenue"]]
                    .sort_values(["Product"])
                )
                st.markdown("#### Products to Block")
                st.dataframe(out, use_container_width=True)

                csv_buffer = io.StringIO()
                out.to_csv(csv_buffer, index=False)
                csv_bytes = csv_buffer.getvalue().encode()
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv_bytes,
                    file_name="products_to_block.csv",
                    mime="text/csv"
                )

st.markdown("---")
st.header("🤖 Ask AI About Your Data")
st.markdown(
    """
    Enter a question about your data in natural language. The model will
    respond based on the loaded dataset (e.g., “Show me top discrepancy
    products last week,” or “What’s the average IVT for Advertiser X?”).
    """
)
if "ai_history" not in st.session_state:
    st.session_state["ai_history"] = []

question = st.text_input(
    "Your question:",
    placeholder="e.g. ‘Which advertiser had the highest revenue on May 20?’"
)
ask_button = st.button("Ask AI")

def query_openai(prompt: str, context_df: pd.DataFrame) -> str:
    advs = context_df["Advertiser"].unique().tolist()
    drange = f"{context_df['Date'].min().date()} to {context_df['Date'].max().date()}"
    context_descr = (
        f"Dataset covers advertisers: {', '.join(advs)}; "
        f"Date range: {drange}. Columns: {', '.join(context_df.columns.tolist())}."
    )
    system_msg = (
        "You are a data assistant. Use the provided context description about the dataset. "
        "Answer questions concisely, refer to metrics and columns accurately."
    )
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": f"Context: {context_descr}\nQuestion: {prompt}"}
    ]
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.2,
            max_tokens=250
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ OpenAI API error: {e}"

if ask_button and question:
    with st.spinner("🤖 Asking AI..."):
        answer = query_openai(question, df_filtered)
        st.session_state["ai_history"].append((question, answer))

if st.session_state["ai_history"]:
    for q, a in st.session_state["ai_history"][::-1]:
        st.markdown(f"**Q:** {q}")
        st.markdown(f"**A:** {a}")
        st.markdown("---")
