import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF # fpdf2 library mein bhi import name same hai
import os

# --- PDF GENERATOR CLASS (Updated for fpdf2) ---
class InvoicePDF(FPDF):
    def header(self):
        # Top Strips
        self.set_fill_color(0, 51, 102); self.rect(10, 8, 22, 8, "F")
        self.set_fill_color(0, 153, 224); self.rect(35, 8, 165, 8, "F")
        if os.path.exists("lo.png"): self.image("lo.png", x=10, y=18, w=25)
        self.set_xy(40, 20); self.set_font("Arial", "B", 20); self.set_text_color(20, 40, 80)
        self.cell(0, 10, "Badar Diagnostics & Medical Equipments")

    def footer(self):
        # Dark Blue Footer Background
        self.set_fill_color(0, 51, 102); self.rect(10, 260, 190, 15, "F")
        # Light Blue Contact Line
        self.set_fill_color(0, 153, 224); self.rect(10, 275, 190, 8, "F")
        
        # Office Locations
        self.set_y(262); self.set_text_color(255, 255, 255); self.set_font("Arial", "", 7)
        self.multi_cell(0, 3.5, "Lahore Office: D Block Nawab Town, Lahore   |   Okara Office: Adjacent Ibn-e-Sina Lab, Opposite DHQ, Okara\nPindi Office: Commercial Market, Rawalpindi   |   Bahawalpur Office: Model Town C, Bahawalpur", align="C")
        
        # Contact Info
        self.set_y(276); self.set_font("Arial", "B", 8)
        self.cell(0, 4, " 0300-7303020, 0334-7303020      E-mail: munir.badar1@gmail.com", align="C")

def generate_pdf(row):
    pdf = InvoicePDF()
    pdf.add_page()
    
    # Blue Color Definition
    blue_color = (0, 153, 224)
    
    # 1. Invoice No. Section
    pdf.set_xy(15, 45)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(*blue_color)
    pdf.cell(10, 5, "No.")
    
    pdf.set_text_color(0, 0, 0) # Black color for text
    pdf.set_font("Arial", "", 12)
    pdf.set_xy(25, 45)
    pdf.cell(40, 5, f"{row['invoice_no']}")
    pdf.set_draw_color(*blue_color)
    pdf.line(25, 50, 65, 50) # Blue Underline
    
    # 2. Date Section
    pdf.set_xy(155, 45)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(*blue_color)
    pdf.cell(10, 5, "Date")
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 12)
    pdf.set_xy(165, 45)
    pdf.cell(40, 5, f"{row['date']}")
    pdf.line(165, 50, 195, 50) # Blue Underline
    
    # 3. Client Name
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(15, 58)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, f"To: {row['client']}")
    
    # Title
    pdf.set_xy(0, 70)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(210, 8, "INVOICE", align="C")

    # Table Header
    y = 85
    pdf.set_xy(25, y)
    pdf.set_font("Arial", "B", 9); pdf.set_fill_color(240, 240, 240)
    pdf.cell(15, 8, "SR #", 1, 0, "C", True)
    pdf.cell(45, 8, "PRODUCT", 1, 0, "C", True)
    pdf.cell(40, 8, "SPECS", 1, 0, "C", True) 
    pdf.cell(15, 8, "QTY", 1, 0, "C", True)
    pdf.cell(25, 8, "PRICE", 1, 0, "C", True)
    pdf.cell(25, 8, "TOTAL", 1, 1, "C", True)

    # Table Data Row
    pdf.set_font("Arial", "", 9); pdf.set_x(25)
    pdf.cell(15, 8, "1", 1, 0, "C")
    pdf.cell(45, 8, str(row['equipment']), 1)
    pdf.cell(40, 8, str(row['specs']), 1) 
    pdf.cell(15, 8, str(row['quantity']), 1, 0, "C")
    pdf.cell(25, 8, f"{row['unit_price']:.0f}", 1, 0, "C")
    pdf.cell(25, 8, f"{row['close_deal']:.0f}", 1, 1, "C")

    # Grand Total
    pdf.set_x(125); pdf.set_font("Arial", "B", 10)
    pdf.cell(40, 8, "Grand Total", 1, 0, "C", True)
    pdf.cell(25, 8, f"{row['close_deal']:.0f}", 1, 1, "C", True)
    
    file_path = f"Invoice_{row['invoice_no']}.pdf"
    # --- Footer Section Layout ---
    # Footer se thoda upar line draw karna (y=222)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, 222, 200, 222) 

    # --- Regards & Account Details (Left side, y=225) ---
    pdf.set_xy(15, 225)
    pdf.set_font("Arial", "I", 9)
    pdf.cell(90, 5, "Regards,", ln=1)
    
    pdf.set_x(15)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(90, 5, "Badar Diagnostics & Medical Equipment, Lahore", ln=1)
    
    pdf.set_x(15)
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(0, 51, 102) # Dark Blue
    pdf.cell(90, 5, "Account Details:", ln=1)
    
    pdf.set_x(15)
    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(0, 0, 0) # Black
    pdf.multi_cell(90, 4, "Badar Diagnostics & Medical Equipment\nFaysal Bank\n0155007000005585")

    # --- Stamp (Right side, y=225) ---
    if os.path.exists("stamp.jpg"):
        # Stamp ko text ke barabar set kiya hai
        pdf.image("stamp.jpg", x=140, y=225, w=35)
    
    # Save the file
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
        # Total Revenue Metric
        st.metric("Total Revenue", f"Rs {int(st.session_state.business_df['close_deal'].sum()):,}")
        
        # Plotly Chart with explicit px import check
        try:
            fig = px.bar(st.session_state.business_df, x='invoice_no', y='close_deal', template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        except NameError:
            st.error("Plotly is not installed or loaded correctly. Please add 'plotly' to your requirements.txt.")
