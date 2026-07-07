import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from fpdf import FPDF
from datetime import datetime

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('enterprise.db')
    c = conn.cursor()
    # Table for Home Finance
    c.execute('''CREATE TABLE IF NOT EXISTS home_finance 
                 (id INTEGER PRIMARY KEY, recipient TEXT, amount REAL)''')
    # Table for Business Deals
    c.execute('''CREATE TABLE IF NOT EXISTS business_deals 
                 (id INTEGER PRIMARY KEY, date TEXT, client TEXT, invoice_no TEXT, 
                  specs TEXT, quantity REAL, unit_price REAL, total REAL, 
                  cost REAL, paid REAL, remaining REAL, type TEXT)''')
    conn.commit()
    conn.close()

# Initialize DB
init_db()

st.set_page_config(page_title="Hameez Enterprise Hub", layout="wide")

# CSS
st.markdown("""
    <style>
    .stApp {background-color: #05070a;}
    h1, h2 {color: #00f2ff !important;}
    </style>
""", unsafe_allow_html=True)

# --- PDF FUNCTION ---
def download_pdf(row):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "HAMEEZ ENTERPRISE INVOICE", 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    for col in row.index:
        pdf.cell(0, 10, f"{col.upper()}: {row[col]}", 0, 1)
    return pdf.output(dest='S').encode('latin-1')

tab1, tab2, tab3, tab4 = st.tabs(["🏠 Home Finance", "💼 Business Deals", "💳 Credit/Debit Sheets", "📊 Analytics"])

# --- TAB 1: Home Finance (Same as your original) ---
with tab1:
    st.title("🏡 Home Finance Tracker")
    conn = sqlite3.connect('enterprise.db')
    if 'home_init' not in st.session_state:
        st.session_state.home_df = pd.read_sql("SELECT * FROM home_finance", conn)
        st.session_state.home_init = True
    
    with st.expander("➕ Add Home Transaction"):
        with st.form("home_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            recipient = col_a.selectbox("Who received it?", ["Anoushay", "Hameez", "Talha", "Self", "General House", "Sent to Home"])
            amount = col_b.number_input("Amount (Rs)", min_value=0, step=1)
            if st.form_submit_button("Update Home Finance"):
                conn.execute("INSERT INTO home_finance (recipient, amount) VALUES (?,?)", (recipient, amount))
                conn.commit()
                st.rerun()
    
    df_home = pd.read_sql("SELECT * FROM home_finance", conn)
    st.dataframe(df_home, use_container_width=True)
    conn.close()

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
    )
# --- TAB 3: Credit/Debit Sheets ---
with tab3:
    st.title("💳 Credit & Debit Records")
    df = pd.read_sql("SELECT * FROM business_deals", sqlite3.connect('enterprise.db'))
    
    st.subheader("Credit Sheet (Receivables)")
    st.dataframe(df[['client', 'invoice_no', 'total', 'paid', 'remaining']], use_container_width=True)
    
    st.subheader("Debit Sheet (Liabilities)")
    st.dataframe(df[['client', 'invoice_no', 'total', 'paid', 'remaining']], use_container_width=True)

    # PDF Download Logic
    selected_idx = st.selectbox("Select Invoice No to Download", df['invoice_no'].unique())
    if st.button("Download PDF"):
        row = df[df['invoice_no'] == selected_idx].iloc[0]
        st.download_button("Click to Download", download_pdf(row), f"{selected_idx}.pdf", "application/pdf")

# --- TAB 4: Analytics ---
with tab4:
    st.title("📊 Performance Insights")
    df_biz = pd.read_sql("SELECT * FROM business_deals", sqlite3.connect('enterprise.db'))
    if not df_biz.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Revenue", f"Rs {df_biz['total'].sum():,}")
        col2.metric("Total Profit", f"Rs {(df_biz['total'] - df_biz['cost']).sum():,}")
        col3.metric("Outstanding", f"Rs {df_biz['remaining'].sum():,}")
        
        st.subheader("Cost vs Profit")
        fig = px.bar(df_biz, x='invoice_no', y=['cost', 'total'], barmode='group', template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
