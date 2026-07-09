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
        self.multi_cell(0, 3.5, "Lahore Office: D Block Nawab Town, Lahore   |   Okara Office: Adjacent Ibn-e-Sina Lab, Opposite DHQ, Okara\nRawalpindi Office: Commercial Market, Rawalpindi   |   Bahawalpur Office: Model Town C, Bahawalpur", align="C")
        
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
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 12)
    inv_text = f"{row['invoice_no']}"
    pdf.set_xy(25, 45)
    pdf.cell(pdf.get_string_width(inv_text), 5, inv_text)
    
    # Underline exactly as long as text
    pdf.set_draw_color(*blue_color)
    pdf.line(25, 50, 25 + pdf.get_string_width(inv_text), 50)
    
    # 2. Date Section (Gap ke sath)
    date_label = "Date"
    date_val = f"{row['date']}"
    
    pdf.set_xy(140, 45) # Position adjust ki
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(*blue_color)
    pdf.cell(10, 5, date_label)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 12)
    # Gap ke liye x coordinate thoda aage badhaya
    date_x = 140 + pdf.get_string_width(date_label) + 5 
    pdf.set_xy(date_x, 45)
    pdf.cell(pdf.get_string_width(date_val), 5, date_val)
    
    # Date Underline
    pdf.line(date_x, 50, date_x + pdf.get_string_width(date_val), 50)
    
    # 3. Client Name (Underline ke sath)
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(15, 58)
    pdf.set_font("Arial", "B", 12)
    client_label = "To: "
    client_name = f"{row['client']}"
    
    pdf.cell(pdf.get_string_width(client_label), 6, client_label)
    pdf.set_font("Arial", "", 12)
    pdf.cell(pdf.get_string_width(client_name), 6, client_name)
    
    # Client Name Underline
    pdf.set_draw_color(0, 0, 0) # Black underline for client
    pdf.line(15 + pdf.get_string_width(client_label), 64, 
             15 + pdf.get_string_width(client_label) + pdf.get_string_width(client_name), 64)    
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
    c.execute('''CREATE TABLE IF NOT EXISTS business_deals (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, invoice_no TEXT, client TEXT, equipment TEXT, specs TEXT, unit_price REAL, quantity REAL, close_deal REAL, unit_actual_cost REAL, actual_cost REAL, paid REAL, remaining REAL, profit REAL, team_member TEXT, status TEXT)''')
    conn.commit(); conn.close()

init_db()
st.set_page_config(page_title="Hameez Enterprise Hub", layout="wide")

if 'business_df' not in st.session_state:
    conn = sqlite3.connect('enterprise.db')
    st.session_state.business_df = pd.read_sql("SELECT * FROM business_deals", conn); conn.close()
    st.session_state.business_df['id'] = range(1, len(st.session_state.business_df) + 1)

tabs = st.tabs(["🏠 Home Finance", "💼 Business Deals", "💳 Credit/Debit Sheets", "📊 Analytics"])
tab1, tab2, tab3, tab4 = tabs

with tab2:
    st.title("➕ Register Medical Invoice")
    
    # Session state initialize karein
    if 'temp_items' not in st.session_state:
        st.session_state.temp_items = []

    with st.form("add_product_form"):
        c1, c2 = st.columns(2)
        equipment = c1.text_input("Equipment")
        specs = c2.text_input("SPECS")
        c3, c4 = st.columns(2)
        qty = c3.number_input("QUANTITY", min_value=0.0, format="%g")
        u_price = c4.number_input("Unit Price", min_value=0.0, format="%g")
        
        if st.form_submit_button("➕ Add Product to Invoice"):
            item = {"equipment": equipment, "specs": specs, "qty": qty, "price": u_price, "total": qty * u_price}
            st.session_state.temp_items.append(item)
            st.rerun()

    # Show items
    if st.session_state.temp_items:
        st.write("### Invoice Items:")
        temp_df = pd.DataFrame(st.session_state.temp_items)
        st.table(temp_df)
        
        # Invoice Finalize form
        with st.form("finalize_invoice"):
            client = st.text_input("Client Name")
            paid = st.number_input("Payment Received", min_value=0.0)
            
            if st.form_submit_button("✅ Finalize & Save Invoice"):
                inv_no = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                total_sum = temp_df['total'].sum()
                
                conn = sqlite3.connect('enterprise.db')
                # Note: Aapke database schema mein ek row per invoice hai, 
                # yahan hum har item ko save kar rahe hain (ya total sum)
                conn.execute("INSERT INTO business_deals (date, invoice_no, client, equipment, specs, unit_price, quantity, close_deal, status) VALUES (?,?,?,?,?,?,?,?,?)",
                             (datetime.now().strftime("%Y-%m-%d"), inv_no, client, "Multiple Items", "See Details", 0, 0, total_sum, "Paid"))
                conn.commit(); conn.close()
                
                st.session_state.temp_items = [] # Reset list
                st.success("Invoice Saved Successfully!")
                st.rerun()
    
    if st.button("🗑️ Clear List"):
        st.session_state.temp_items = []
        st.rerun()    st.subheader("📋 Records"); st.dataframe(st.session_state.business_df, use_container_width=True, hide_index=True)
    
    st.divider(); st.subheader("🖨️ Generate Invoice PDF")
    selected_id = st.selectbox("Select ID to Download:", st.session_state.business_df['id'].tolist())
    if st.button("Generate & Download"):
        row = st.session_state.business_df[st.session_state.business_df['id'] == selected_id].iloc[0]
        path = generate_pdf(row)
        with open(path, "rb") as f: st.download_button("✅ Download PDF Now", f, file_name=path)
