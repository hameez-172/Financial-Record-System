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

# --- Session State Initialization ---
if 'home_df' not in st.session_state:
    st.session_state.home_df = pd.DataFrame({'Recipient': ['Anoushay', 'Hameez', 'Talha', 'Self', 'General House', 'Sent to Home'], 'Amount': [0, 0, 0, 0, 0, 0]})

if 'business_df' not in st.session_state:
    st.session_state.business_df = pd.DataFrame(columns=['Date', 'Client', 'Equipment', 'Deal Value', 'Cost', 'Sent Payment', 'Remaining', 'Profit', 'Team Member', 'Status'])

tab1, tab2, tab3 = st.tabs(["🏠 Home Finance", "💼 Business Deals", "📊 Business Analytics"])

# --- TAB 1: Home Finance ---
with tab1:
    st.title("🏡 Home Finance Tracker")
    df = st.session_state.home_df
    totals = df.groupby('Recipient')['Amount'].sum()
    
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
# --- TAB 2: Business Deals ---
with tab2:
    st.title("➕ Register & Manage Medical Deal")
    # [Form logic same yahan rahegi]
    with st.form("biz_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        client = c1.text_input("Client Name")
        equip = c2.text_input("Equipment")
        team_member = c3.text_input("Team Member (Optional)")
        c4, c5, c6 = st.columns(3)
        deal_val = c4.number_input("Total Deal Value", min_value=0, step=1)
        cost = c5.number_input("Actual Cost", min_value=0, step=1)
        sent_pay = c6.number_input("Payment Sent", min_value=0, step=1)
        if st.form_submit_button("Log Deal"):
            remaining = int(deal_val - sent_pay)
            profit = int(deal_val - cost)
            status = "Paid" if remaining <= 0 else "Pending"
            new_row = pd.DataFrame([{'Date': pd.Timestamp.now().strftime("%Y-%m-%d"), 'Client': client, 'Equipment': equip, 'Deal Value': int(deal_val), 'Cost': int(cost), 'Sent Payment': int(sent_pay), 'Remaining': remaining, 'Profit': profit, 'Team Member': team_member if team_member else "N/A", 'Status': status}])
            st.session_state.business_df = pd.concat([st.session_state.business_df, new_row], ignore_index=True)
            st.rerun()

    st.subheader("📋 Recent Deals (Edit Remaining to 0 to Pay)")

    # 1. Editor jisme edit kar saken
    edited_df = st.data_editor(
        st.session_state.business_df, 
        use_container_width=True, 
        hide_index=True,
        key="data_editor_main"
    )

    # 2. Logic: Agar koi change hui to recalculate aur status update
    if not edited_df.equals(st.session_state.business_df):
        # Remaining manually 0 karne par Status "Paid" ho jayega
        edited_df["Status"] = edited_df["Remaining"].apply(lambda x: "Paid" if x <= 0 else "Pending")
        st.session_state.business_df = edited_df
        st.rerun()

    # 3. Highlight Function: Sirf wahan red hoga jahan Remaining > 0
    def highlight_remaining(val):
        color = '#ff4b4b' if isinstance(val, (int, float)) and val > 0 else ''
        return f'background-color: {color}'

    # 4. Display Table: Yeh sirf show karne ke liye hai (styling ke sath)
    st.dataframe(
        st.session_state.business_df.style.map(highlight_remaining, subset=['Remaining']),
        use_container_width=True
    )    # --- TAB 3: Business Analytics ---
with tab3:
    st.title("📊 Performance Insights")
    if not st.session_state.business_df.empty:
        df_biz = st.session_state.business_df
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Revenue", f"Rs {int(df_biz['Deal Value'].sum()):,}")
        m2.metric("Total Profit", f"Rs {int(df_biz['Profit'].sum()):,}")
        m3.metric("Outstanding", f"Rs {int(df_biz['Remaining'].sum()):,}")
        m4.metric("Margin", f"{((df_biz['Profit'].sum()/df_biz['Deal Value'].sum())*100):.1f}%" if df_biz['Deal Value'].sum() > 0 else "0%")

        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("Cost vs Profit")
            fig = px.bar(df_biz, x='Equipment', y=['Cost', 'Profit'], barmode='group', template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        with col_right:
            st.subheader("Remaining Payment")
            fig_pie = px.pie(df_biz, values='Remaining', names='Client', hole=0.5, template="plotly_dark")
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Log a deal to see analytics.")
