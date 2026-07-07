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
    with st.form("biz_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        doc_type = c1.selectbox("Type", ["Invoice", "Quotation"])
        inv_no = c2.text_input("Invoice No")
        client = c3.text_input("Client Name")
        specs = st.text_input("SPECS")
        c4, c5, c6 = st.columns(3)
        qty = c4.number_input("QUANTITY", min_value=0)
        u_price = c5.number_input("PER UNIT PRICE", min_value=0)
        cost = c6.number_input("Actual Cost", min_value=0)
        paid = st.number_input("Payment Paid", min_value=0)
        
        if st.form_submit_button("Log Deal"):
            total = qty * u_price
            rem = total - paid
            conn = sqlite3.connect('enterprise.db')
            conn.execute("INSERT INTO business_deals (date, client, invoice_no, specs, quantity, unit_price, total, cost, paid, remaining, type) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                         (datetime.now().strftime("%Y-%m-%d"), client, inv_no, specs, qty, u_price, total, cost, paid, rem, doc_type))
            conn.commit()
            conn.close()
            st.rerun()

    df_biz = pd.read_sql("SELECT * FROM business_deals", sqlite3.connect('enterprise.db'))
    st.dataframe(df_biz, use_container_width=True)

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
