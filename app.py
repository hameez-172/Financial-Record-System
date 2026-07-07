import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hameez Finance Hub", layout="wide")

# Professional CSS Styling
st.markdown("""
    <style>
    .stApp {background-color: #0b0e14;}
    .metric-card {background: #1e1e24; padding: 20px; border-radius: 15px; border: 1px solid #444; text-align: center;}
    h1, h2, h3 {color: #00d4ff !important;}
    .stDataFrame {border: 1px solid #444;}
    </style>
""", unsafe_allow_html=True)

# Session State for Real-Time Updates
if 'home_df' not in st.session_state:
    st.session_state.home_df = pd.DataFrame({
        'Recipient': ['Anoushay', 'Hameez', 'Talha'],
        'Amount': [10000, 5000, 8000]
    })

tab1, tab2 = st.tabs(["🏠 Home Dashboard", "💼 Business Dashboard"])

with tab1:
    st.title("🏡 Home Finance Tracker")
    
    # --- Real-time Metrics ---
    df = st.session_state.home_df
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Anoushay", f"Rs {df[df['Recipient']=='Anoushay']['Amount'].sum():,}")
    c2.metric("Hameez", f"Rs {df[df['Recipient']=='Hameez']['Amount'].sum():,}")
    c3.metric("Talha", f"Rs {df[df['Recipient']=='Talha']['Amount'].sum():,}")
    c4.metric("Total Sent", f"Rs {df['Amount'].sum():,}")

    # --- Add New Entry ---
    with st.expander("➕ Click to Add New Home Transaction", expanded=True):
        with st.form("home_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            recipient = col_a.selectbox("Who received it?", ["Anoushay", "Hameez", "Talha", "General House"])
            amount = col_b.number_input("Amount (Rs)", min_value=0)
            
            if st.form_submit_button("Update Dashboard"):
                new_data = pd.DataFrame({'Recipient': [recipient], 'Amount': [amount]})
                st.session_state.home_df = pd.concat([st.session_state.home_df, new_data], ignore_index=True)
                st.rerun() # Yeh command foran dashboard ko refresh karegi

    # --- Visuals ---
    col_chart1, col_chart2 = st.columns([1, 1])
    
    with col_chart1:
        st.subheader("Transaction Log")
        st.dataframe(st.session_state.home_df, use_container_width=True)

    with col_chart2:
        st.subheader("Distribution Analysis")
        fig = px.pie(st.session_state.home_df, values='Amount', names='Recipient', 
                     hole=0.6, color_discrete_sequence=px.colors.qualitative.Dark24)
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.title("💼 Business Finance")
    st.info("Business module is being integrated...")
