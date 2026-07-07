import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hameez Finance Hub", layout="wide")

# Professional CSS Styling
st.markdown("""
    <style>
    .stApp {background-color: #0b0e14;}
    h1, h2, h3 {color: #00d4ff !important;}
    .stDataFrame {border: 1px solid #444;}
    </style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if 'home_df' not in st.session_state:
    st.session_state.home_df = pd.DataFrame({
        'Recipient': ['Anoushay', 'Hameez', 'Talha', 'Self', 'General House', 'Sent to Home'], 
        'Amount': [0, 0, 0, 0, 0, 0]
    })

if 'business_df' not in st.session_state:
    st.session_state.business_df = pd.DataFrame(columns=[
        'Date', 'Client', 'Equipment', 'Deal Value', 'Cost', 'Profit', 'Team Member', 'Status'
    ])

tab1, tab2 = st.tabs(["🏠 Home Dashboard", "💼 Medical Business Dashboard"])

# --- TAB 1: Home Dashboard ---
with tab1:
    st.title("🏡 Home Finance Tracker")
    df = st.session_state.home_df
    totals = df.groupby('Recipient')['Amount'].sum()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Anoushay", f"Rs {totals.get('Anoushay', 0):,}")
    c2.metric("Hameez", f"Rs {totals.get('Hameez', 0):,}")
    c3.metric("Talha", f"Rs {totals.get('Talha', 0):,}")
    c4.metric("Self", f"Rs {totals.get('Self', 0):,}")
    
    c5, c6, c7 = st.columns(3)
    c5.metric("General House", f"Rs {totals.get('General House', 0):,}")
    c6.metric("Sent to Home", f"Rs {totals.get('Sent to Home', 0):,}")
    c7.metric("Total Spent", f"Rs {df['Amount'].sum():,}")

    with st.expander("➕ Add New Home Transaction"):
        with st.form("home_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            options = ["Anoushay", "Hameez", "Talha", "Self", "General House", "Sent to Home"]
            recipient = col_a.selectbox("Who received it?", options)
            amount = col_b.number_input("Amount (Rs)", min_value=0)
            if st.form_submit_button("Update Dashboard"):
                new_data = pd.DataFrame({'Recipient': [recipient], 'Amount': [amount]})
                st.session_state.home_df = pd.concat([st.session_state.home_df, new_data], ignore_index=True)
                st.rerun()

    col_chart1, col_chart2 = st.columns([1, 1])
    with col_chart1:
        st.subheader("Transaction Log")
        st.dataframe(st.session_state.home_df, use_container_width=True)
    with col_chart2:
        st.subheader("Distribution Analysis")
        fig = px.pie(values=totals.values, names=totals.index, hole=0.6, color_discrete_sequence=px.colors.qualitative.Dark24)
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: Medical Business Dashboard ---
with tab2:
    st.title("💼 Medical Equipment Business")
    
    with st.expander("➕ Register New Medical Deal", expanded=True):
        with st.form("biz_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            client = col1.text_input("Client Name")
            equip = col2.text_input("Equipment Name")
            status = col3.selectbox("Status", ["Paid", "Pending"])
            
            col4, col5, col6 = st.columns(3)
            deal_val = col4.number_input("Deal Value (Rs)", min_value=0.0)
            cost = col5.number_input("Cost/Investment (Rs)", min_value=0.0)
            team_member = col6.text_input("Team Member Involved")
            
            if st.form_submit_button("Log Deal"):
                profit = deal_val - cost
                new_deal = pd.DataFrame([{
                    'Date': pd.Timestamp.now().strftime("%Y-%m-%d"),
                    'Client': client, 'Equipment': equip, 'Deal Value': deal_val,
                    'Cost': cost, 'Profit': profit, 'Team Member': team_member, 'Status': status
                }])
                st.session_state.business_df = pd.concat([st.session_state.business_df, new_deal], ignore_index=True)
                st.rerun()

    if not st.session_state.business_df.empty:
        df_biz = st.session_state.business_df
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Revenue", f"Rs {df_biz['Deal Value'].sum():,}")
        m2.metric("Net Profit", f"Rs {df_biz['Profit'].sum():,}")
        m3.metric("Outstanding (Pending)", f"Rs {df_biz[df_biz['Status'] == 'Pending']['Deal Value'].sum():,}")
        
        st.subheader("Recent Deal Log")
        st.dataframe(df_biz, use_container_width=True)
        
        st.subheader("Profitability Analysis")
        fig_biz = px.pie(df_biz, values='Profit', names='Equipment', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_biz.update_layout(template="plotly_dark")
        st.plotly_chart(fig_biz, use_container_width=True)
    else:
        st.info("No business deals registered yet. Add your first medical equipment deal above!")
