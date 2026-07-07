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
    c.execute('''CREATE TABLE IF NOT EXISTS home_finance (id INTEGER PRIMARY KEY, recipient TEXT, amount REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS business_deals 
                 (id INTEGER PRIMARY KEY, date TEXT, client TEXT, invoice_no TEXT, 
                  specs TEXT, quantity REAL, unit_price REAL, total REAL, 
                  cost REAL, paid REAL, remaining REAL, type TEXT, status TEXT)''')
    conn.commit()
    conn.close()

init_db()

st.set_page_config(page_title="Hameez Enterprise Hub", layout="wide")

# --- PDF FUNCTION ---
def download_pdf(row):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "HAMEEZ ENTERPRISE INVOICE", 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    for col, val in row.items():
        pdf.cell(0, 10, f"{col.upper()}: {val}", 0, 1)
    return pdf.output(dest='S').encode('latin-1')

tab1, tab2, tab3, tab4 = st.tabs(["🏠 Home Finance", "💼 Business Deals", "💳 Credit/Debit Sheets", "📊 Analytics"])

# --- TAB 1: Home Finance ---
with tab1:
    st.title("🏡 Home Finance Tracker")
    conn = sqlite3.connect('enterprise.db')
    if st.button("Add Home Data"):
        conn.execute("INSERT INTO home_finance (recipient, amount) VALUES ('General', 0)")
        conn.commit()
    st.dataframe(pd.read_sql("SELECT * FROM home_finance", conn), use_container_width=True)
    conn.close()

# --- TAB 2: Business Deals (WITH DATA EDITOR) ---
with tab2:
    st.title("➕ Register & Manage Medical Deal")
    
    # Form to add new deal
    with st.form("biz_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        inv_no = c1.text_input("Invoice No")
        client = c2.text_input("Client Name")
        specs = c3.text_input("SPECS")
        c4, c5, c6 = st.columns(3)
        qty = c4.number_input("QUANTITY", min_value=0.0)
        u_price = c5.number_input("PER UNIT PRICE", min_value=0.0)
        cost = c6.number_input("Actual Cost", min_value=0.0)
        paid = st.number_input("Payment Paid", min_value=0.0)
        
        if st.form_submit_button("Log Deal"):
            total = qty * u_price
            rem = total - paid
            status = "Paid" if rem <= 0 else "Pending"
            conn = sqlite3.connect('enterprise.db')
            conn.execute("INSERT INTO business_deals (date, client, invoice_no, specs, quantity, unit_price, total, cost, paid, remaining, type, status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                         (datetime.now().strftime("%Y-%m-%d"), client, inv_no, specs, qty, u_price, total, cost, paid, rem, "Invoice", status))
            conn.commit()
            conn.close()
            st.rerun()

    # Data Editor for Editing Deals
    conn = sqlite3.connect('enterprise.db')
    df_biz = pd.read_sql("SELECT * FROM business_deals", conn)
    
    st.subheader("📋 Edit Recent Deals")
    edited_df = st.data_editor(df_biz, use_container_width=True, key="editor_1")
    
    if st.button("Save Changes to Database"):
        # Recalculate logic for updated rows
        edited_df['remaining'] = edited_df['total'] - edited_df['paid']
        edited_df['status'] = edited_df['remaining'].apply(lambda x: "Paid" if x <= 0 else "Pending")
        
        # Save back to SQL
        edited_df.to_sql('business_deals', conn, if_exists='replace', index=False)
        st.success("Database Updated Successfully!")
        st.rerun()
    conn.close()

# --- TAB 3: Credit/Debit Sheets ---
with tab3:
    st.title("💳 Financial Sheets")
    conn = sqlite3.connect('enterprise.db')
    df = pd.read_sql("SELECT * FROM business_deals", conn)
    conn.close()
    
    if not df.empty:
        # Check karein ke columns exist karte hain ya nahi
        required_cols = ['client', 'invoice_no', 'total', 'paid', 'remaining', 'status']
        # Jo columns missing hain, unhein ignore ya create karein
        existing_cols = [c for c in required_cols if c in df.columns]
        
        st.subheader("Credit Sheet (Receivables)")
        st.dataframe(df[existing_cols], use_container_width=True)
        
        st.subheader("Debit Sheet (Liabilities)")
        st.dataframe(df[['client', 'invoice_no', 'cost', 'paid']], use_container_width=True)
    else:
        st.write("Abhi koi data enter nahi hua.")
# --- TAB 4: Analytics ---
with tab4:
    st.title("📊 Performance Insights")
    conn = sqlite3.connect('enterprise.db')
    df_biz = pd.read_sql("SELECT * FROM business_deals", conn)
    if not df_biz.empty:
        st.metric("Total Revenue", f"Rs {df_biz['total'].sum():,}")
        fig = px.bar(df_biz, x='invoice_no', y='total', template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    conn.close()
