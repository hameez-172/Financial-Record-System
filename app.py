import streamlit as st

import pandas as pd

import plotly.express as px



st.set_page_config(page_title="Hameez Finance Hub", layout="wide")



# Styling

st.markdown("""

    <style>

    .stApp {background-color: #0b0e14;}

    .metric-card {background: #1e1e24; padding: 15px; border-radius: 10px; border: 1px solid #333;}

    </style>

""", unsafe_allow_html=True)



# Tabs setup

tab1, tab2 = st.tabs(["🏠 Home Dashboard", "💼 Business Dashboard"])



# --- HOME DASHBOARD DATA ---

home_data = {

    'Date': ['2026-07-01', '2026-07-02', '2026-07-03'],

    'Recipient': ['Anoushay', 'Hameez', 'Talha'],

    'Amount': [10000, 5000, 8000],

    'Type': ['Sent to Home', 'Self-Transfer', 'Education']

}

df_home = pd.DataFrame(home_data)



with tab1:

    st.title("🏡 Home Finance Tracker")

    

    # Metrics for Home

    c1, c2, c3 = st.columns(3)

    c1.metric("Total Sent to Home", f"Rs {df_home[df_home['Recipient']=='Anoushay']['Amount'].sum():,}")

    c2.metric("Hameez Personal", f"Rs {df_home[df_home['Recipient']=='Hameez']['Amount'].sum():,}")

    c3.metric("Talha Expenses", f"Rs {df_home[df_home['Recipient']=='Talha']['Amount'].sum():,}")



    # Detailed Table for Home

    st.subheader("Transaction Log")

    st.dataframe(df_home, use_container_width=True)



    # Visualization

    fig_home = px.pie(df_home, values='Amount', names='Recipient', title="Distribution of Funds", hole=0.5, template="plotly_dark")

    st.plotly_chart(fig_home, use_container_width=True)



    # Specific Add Entry for Home

    with st.expander("➕ Add New Home Entry"):

        with st.form("home_form"):

            r = st.selectbox("Who received it?", ["Anoushay", "Hameez", "Talha", "General House"])

            a = st.number_input("Amount", min_value=0)

            if st.form_submit_button("Submit"):

                st.success(f"Added Rs {a} for {r}")



# --- BUSINESS DASHBOARD ---

with tab2:

    st.title("💼 Business Finance")

    st.info("Business dashboard under construction. Stay tuned!")
