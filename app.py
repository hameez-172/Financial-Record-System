import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime
from fpdf import FPDF
import os
import random

# --- PDF GENERATOR CLASS (Aapka Design) ---
class InvoicePDF(FPDF):
    def header(self):
        self.set_fill_color(0, 51, 102); self.rect(10, 8, 22, 8, "F")
        self.set_fill_color(0, 153, 224); self.rect(35, 8, 165, 8, "F")
        if os.path.exists("lo.png"): self.image("lo.png", x=8, y=17, w=30)
        self.set_xy(42, 20); self.set_font("Arial", "B", 20); self.set_text_color(20, 40, 80)
        self.cell(0, 10, "Badar Diagnostics & Medical Equipments"); self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_fill_color(0, 51, 102); self.rect(10, 265, 190, 15, "F")
        self.set_fill_color(0, 153, 224); self.rect(10, 280, 190, 8, "F")
        self.set_y(268); self.set_text_color(255, 255, 255); self.set_font("Arial", "", 7)
        self.multi_cell(0, 4, "Lahore Office: D Block Nawab Town, Lahore | Okara Office: Opposite DHQ | Pindi Office: Commercial Market | Bahawalpur Office: Model Town C", align="C")

def generate_pdf(row):
    pdf = InvoicePDF()
    pdf.add_page()
    # Header Details
    pdf.set_font("Arial", "", 10)
    pdf.set_xy(15, 45); pdf.cell(0, 5, f"Invoice No: {row['invoice_no']}")
    pdf.set_xy(160, 45); pdf.cell(0, 5, f"Date: {row['date']}")
    pdf.set_xy(15, 58); pdf.set_font("Arial", "B", 12); pdf.cell(0, 6, f"To: {row['client']}")
    
    # Product Table
    pdf.set_xy(25, 85); pdf.set_font("Arial", "B", 9); pdf.set_fill_color(240, 240, 240)
    pdf.cell(15, 8, "SR #", 1, 0, "C", True); pdf.cell(80, 8, "EQUIPMENT", 1, 0, "C", True)
    pdf.cell(20, 8, "QTY", 1, 0, "C", True); pdf.cell(30, 8, "PRICE", 1, 0, "C", True)
    pdf.cell(30, 8, "TOTAL", 1, 1, "C", True)
    
    pdf.set_font("Arial", "", 9); pdf.set_x(25)
    pdf.cell(15, 8, "1", 1, 0, "C"); pdf.cell(80, 8, str(row['equipment']), 1)
    pdf.cell(20, 8, str(row['quantity']), 1, 0, "C"); pdf.cell(30, 8, f"{row['unit_price']:.0f}", 1, 0, "C")
    pdf.cell(30, 8, f"{row['close_deal']:.0f}", 1, 1, "C")
    
    # Stamp
    if os.path.exists("stamp.png"): pdf.image("stamp.png", x=140, y=215, w=45)
    
    file_path = f"Invoice_{row['invoice_no']}.pdf"
    pdf.output(file_path)
    return file_path

# --- APP SETUP ---
def init_db():
    conn = sqlite3.connect('enterprise.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS business_deals 
                  (id INTEGER PRIMARY KEY, date TEXT, invoice_no TEXT, client TEXT, equipment TEXT, specs TEXT, 
                  unit_price REAL, quantity REAL, close_deal REAL, unit_actual_cost REAL, actual_cost REAL, 
                  paid REAL, remaining REAL, profit REAL, team_member TEXT, status TEXT)''')
    conn.commit(); conn.close()

init_db()
st.set_page_config(page_title="Hameez Enterprise Hub", layout="wide")

if 'business_df' not in st.session_state:
    conn = sqlite3.connect('enterprise.db')
    st.session_state.business_df = pd.read_sql("SELECT * FROM business_deals", conn); conn.close()

tab1, tab2, tab3, tab4 = st.tabs(["🏠 Home Finance", "💼 Business Deals", "💳 Credit/Debit Sheets", "📊 Analytics"])

with tab2:
    st.title("➕ Register & Manage Medical Deal")
    with st.form("biz_form", clear_on_submit=True):
        c1, c2 = st.columns(2); client = c1.text_input("Client Name/Hospital"); team_member = c2.text_input("Team Member (Optional)")
        c3, c4, c5, c6 = st.columns(4); specs = c3.text_input("SPECS"); equipment = c4.text_input("Equipment")
        qty = c5.number_input("QUANTITY", min_value=0.0, format="%g"); u_price = c6.number_input("Unit Price", min_value=0.0, format="%g")
        c7, c8 = st.columns(2); unit_actual_cost = c7.number_input("Per Unit Actual Cost", min_value=0.0, format="%g"); paid = c8.number_input("Payment sent by Client", min_value=0.0, format="%g")
        
        if st.form_submit_button("Log Deal"):
            inv_no = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"; close_deal = u_price * qty; actual_cost = unit_actual_cost * qty; remaining = close_deal - paid; profit = close_deal - actual_cost; status = "Paid" if remaining <= 0 else "Pending"
            conn = sqlite3.connect('enterprise.db')
            conn.execute("INSERT INTO business_deals (date, invoice_no, client, equipment, specs, unit_price, quantity, close_deal, unit_actual_cost, actual_cost, paid, remaining, profit, team_member, status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                         (datetime.now().strftime("%Y-%m-%d"), inv_no, client, equipment, specs, u_price, qty, close_deal, unit_actual_cost, actual_cost, paid, remaining, profit, team_member, status))
            conn.commit(); st.session_state.business_df = pd.read_sql("SELECT * FROM business_deals", conn); conn.close(); st.rerun()

    st.subheader("📋 Records")
    st.dataframe(st.session_state.business_df, use_container_width=True, hide_index=True)
    
    st.divider(); st.subheader("🖨️ Generate Invoice PDF")
    col_a, col_b = st.columns([0.7, 0.3])
    with col_a:
        selected_id = st.selectbox("Select Deal ID to Download:", st.session_state.business_df['id'].tolist())
    with col_b:
        if st.button("Generate & Download"):
            row = st.session_state.business_df[st.session_state.business_df['id'] == selected_id].iloc[0]
            path = generate_pdf(row)
            with open(path, "rb") as f:
                st.download_button("✅ Download PDF Now", f, file_name=path, mime="application/pdf")

with tab3:
    st.title("💳 Financial Sheets"); st.dataframe(st.session_state.business_df, use_container_width=True)

with tab4:
    st.title("📊 Performance Insights")
    if not st.session_state.business_df.empty:
        st.metric("Total Revenue", f"Rs {int(st.session_state.business_df['close_deal'].sum()):,}")
        st.plotly_chart(px.bar(st.session_state.business_df, x='invoice_no', y='close_deal', template="plotly_dark"), use_container_width=True)
