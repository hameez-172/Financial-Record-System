import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hameez Enterprise Hub", layout="wide")

# Professional CSS
st.markdown("""
    <style>
    .stApp {background-color: #05070a;}
    h1, h2 {color: #00f2ff !important;}
    </style>
""", unsafe_allow_html=True)

# --- Session State ---
if 'home_df' not in st.session_state:
    st.session_state.home_df = pd.DataFrame({'Recipient': ['Anoushay', 'Hameez', 'Talha', 'Self', 'General House', 'Sent to Home'], 'Amount': [0, 0, 0, 0, 0, 0]})

if 'business_df' not in st.session_state:
    st.session_state.business_df = pd.DataFrame(columns=['Date', 'Client', 'Equipment', 'Deal Value', 'Cost', 'Sent Payment', 'Remaining', 'Profit', 'Team Member', 'Status'])

tab1, tab2, tab3 = st.tabs(["🏠 Home Finance", "💼 Business Deals", "📊 Business Analytics"])

# --- TAB 1 ---
with tab1:
    st.title("🏡 Home Finance Tracker")
    totals = st.session_state.home_df.groupby('Recipient')['Amount'].sum()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Anoushay", f"Rs {int(totals.get('Anoushay', 0)):,}")
    c2.metric("Hameez", f"Rs {int(totals.get('Hameez', 0)):,}")
    c3.metric("Talha", f"Rs {int(totals.get('Talha', 0)):,}")
    c4.metric("Self", f"Rs {int(totals.get('Self', 0)):,}")
    
    with st.expander("➕ Add Home Transaction"):
        with st.form("home_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            recipient = col_a.selectbox("Who received it?", ["Anoushay", "Hameez", "Talha", "Self", "General House", "Sent to Home"])
            amount = col_b.number_input("Amount (Rs)", min_value=0, step=1)
            if st.form_submit_button("Update Home Finance"):
                st.session_state.home_df = pd.concat([st.session_state.home_df, pd.DataFrame({'Recipient': [recipient], 'Amount': [int(amount)]})], ignore_index=True)
                st.rerun()
    st.dataframe(st.session_state.home_df.style.format({'Amount': '{:,}'}), use_container_width=True)

# --- TAB 2: Business Deals ---
# --- TAB 2: Business Deals (Final Fixed Version) ---
    st.subheader("📋 Client's Data (Click cell to Edit)")
    
    # 1. Edit ke liye sirf DataFrame use karein (Bina Style ke)
    edited_df = st.data_editor(
        df_filtered,
        use_container_width=True,
        hide_index=True
    )
    
    # 2. Sync Logic (Isme .data ka use nahi hoga)
    if not edited_df.equals(df_filtered):
        # Calculation update
        edited_df['Remaining'] = edited_df['Deal Value'] - edited_df['Sent Payment']
        edited_df['Profit'] = edited_df['Deal Value'] - edited_df['Cost']
        edited_df['Status'] = edited_df['Remaining'].apply(lambda x: "Paid" if x <= 0 else "Pending")
        
        # Session state update
        st.session_state.business_df.update(edited_df)
        st.rerun()

    # 3. Highlighted Table (Sirf Display ke liye)
    def highlight_remaining(val):
        color = '#8b0000' if isinstance(val, (int, float)) and val > 0 else ''
        return f'background-color: {color}'
    
    st.subheader("📊 Recent Deals View")
    st.dataframe(
        df_filtered.style.format({
            'Deal Value': '{:,}', 'Cost': '{:,}', 'Sent Payment': '{:,}', 
            'Remaining': '{:,}', 'Profit': '{:,}'
        }).map(highlight_remaining, subset=['Remaining']), 
        use_container_width=True
    )
# --- TAB 3 ---
with tab3:
    st.title("📊 Performance Insights")
    if not st.session_state.business_df.empty:
        df_biz = st.session_state.business_df
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Revenue", f"Rs {int(df_biz['Deal Value'].sum()):,}")
        m2.metric("Total Profit", f"Rs {int(df_biz['Profit'].sum()):,}")
        m3.metric("Outstanding", f"Rs {int(df_biz['Remaining'].sum()):,}")
        m4.metric("Margin", f"{((df_biz['Profit'].sum()/df_biz['Deal Value'].sum())*100):.1f}%" if df_biz['Deal Value'].sum() > 0 else "0%")
