import streamlit as st
import pandas as pd
from action_center import show_action_center_top10

st.set_page_config(page_title="Revenue Action Center Demo", layout="wide")

st.title("Revenue Action Center")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    show_action_center_top10(df)
else:
    st.info("Please upload your Excel file to see action items.")
