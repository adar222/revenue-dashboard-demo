import streamlit as st
from dashboard import show_revenue_trends

st.set_page_config(page_title="Revenue Insight Dashboard Demo", layout="wide")

st.sidebar.title("Demo Controls")
advertiser = st.sidebar.selectbox("Select Advertiser", ["Magnite", "OpenX", "Pubmatic"])

st.title("Revenue Insight Dashboard (Demo Only)")
show_revenue_trends(advertiser)

# Placeholder for more dashboard sections as you grow:
st.header("More sections coming soon...")
