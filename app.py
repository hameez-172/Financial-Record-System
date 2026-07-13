import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import os
import plotly.express as px

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

def generate_pdf(row, items_df):
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

  # Table Data Rows (Isay replace karein)
    pdf.set_font("Arial", "", 9)
    for index, item in items_df.iterrows():
        pdf.set_x(25)
        pdf.cell(15, 8, str(index + 1), 1, 0, "C")
        pdf.cell(45, 8, str(item['equipment']), 1)
        pdf.cell(40, 8, str(item['specs']), 1) 
        pdf.cell(15, 8, str(item['quantity']), 1, 0, "C")
        pdf.cell(25, 8, f"{item['unit_price']:.0f}", 1, 0, "C")
        pdf.cell(25, 8, f"{item['line_total']:.0f}", 1, 1, "C")

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
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, invoice_no TEXT, client TEXT,
                  close_deal REAL, actual_cost REAL, paid REAL, remaining REAL, profit REAL,
                  team_member TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS deal_items
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, deal_id INTEGER, equipment TEXT, specs TEXT,
                  quantity REAL, unit_price REAL, unit_actual_cost REAL, line_total REAL, line_actual_cost REAL,
                  FOREIGN KEY(deal_id) REFERENCES business_deals(id))''')
    conn.commit(); conn.close()


init_db()
st.set_page_config(page_title="Hameez Enterprise Hub", layout="wide")

if 'business_df' not in st.session_state:
    conn = sqlite3.connect('enterprise.db')
    st.session_state.business_df = pd.read_sql("SELECT * FROM business_deals", conn); conn.close()

if 'temp_items' not in st.session_state:
    st.session_state.temp_items = []

tab1, tab2, tab3, tab4 = st.tabs(["🏠 Home Finance", "💼 Business Deals", "💳 Credit/Debit Sheets", "📊 Analytics"])

# ---------------- TAB 2: BUSINESS DEALS (INTEGRATED) ----------------
with tab2:
    st.title("💼 Business Deals")
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        client = c1.text_input("Client Name/Hospital")
        team_member = c2.text_input("Team Member (Optional)")
        
        c3, c4 = st.columns(2)
        item_name = c3.text_input("Equipment Name")
        item_specs = c4.text_input("Specs")
        
        c5, c6, c7 = st.columns(3)
        item_qty = c5.number_input("Qty", min_value=1, format="%g")
        item_price = c6.number_input("Unit Price", min_value=0.0, format="%g")
        item_cost = c7.number_input("Actual Cost", min_value=0.0, format="%g")
        
        paid = st.number_input("Payment sent by Client", min_value=0.0, format="%g")

    if st.button("➕ Add to List", use_container_width=True):
        if item_name.strip():
            st.session_state.temp_items.append({
                'equipment': item_name, 'specs': item_specs, 'quantity': item_qty,
                'unit_price': item_price, 'unit_actual_cost': item_cost,
                'line_total': item_qty * item_price, 'line_actual_cost': item_qty * item_cost
            })
            st.rerun()
        else:
            st.warning("Equipment Name likhna zaroori hai.")

    with st.form("deal_form", clear_on_submit=True):
        submitted = st.form_submit_button("✅ Log Deal", use_container_width=True)
        if submitted:
            if not st.session_state.temp_items:
                st.error("Pehle kam az kam ek product add karein.")
            elif not client.strip():
                st.error("Client Name zaroori hai.")
            else:
                close_deal = sum(i['line_total'] for i in st.session_state.temp_items)
                actual_cost = sum(i['line_actual_cost'] for i in st.session_state.temp_items)
                remaining = close_deal - paid
                profit = close_deal - actual_cost
                status = "Paid" if remaining <= 0 else "Pending"
                inv_no = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"

                conn = sqlite3.connect('enterprise.db')
                cur = conn.cursor()
                cur.execute("""INSERT INTO business_deals (date, invoice_no, client, close_deal, actual_cost, paid, remaining, profit, team_member, status)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""", (datetime.now().strftime("%Y-%m-%d"), inv_no, client, close_deal, actual_cost, paid, remaining, profit, team_member, status))
                deal_id = cur.lastrowid
                for item in st.session_state.temp_items:
                    cur.execute("""INSERT INTO deal_items (deal_id, equipment, specs, quantity, unit_price, unit_actual_cost, line_total, line_actual_cost)
                        VALUES (?,?,?,?,?,?,?,?)""", (deal_id, item['equipment'], item['specs'], item['quantity'], item['unit_price'], item['unit_actual_cost'], item['line_total'], item['line_actual_cost']))
                conn.commit()
                st.session_state.business_df = pd.read_sql("SELECT * FROM business_deals", conn)
                conn.close()
                st.session_state.temp_items = []
                st.success(f"Deal {inv_no} save ho gayi!")
                st.rerun()

    st.divider()
    st.subheader("📋 Records")
    st.dataframe(st.session_state.business_df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("🖨️ Generate Invoice PDF")
    if not st.session_state.business_df.empty:
        col_a, col_b = st.columns([0.7, 0.3])
        selected_id = col_a.selectbox("Select Deal ID to Download:", st.session_state.business_df['id'].tolist())
        if col_b.button("Generate & Download", use_container_width=True):
            conn = sqlite3.connect('enterprise.db')
            deal_row = st.session_state.business_df[st.session_state.business_df['id'] == selected_id].iloc[0]
            items_df = pd.read_sql("SELECT * FROM deal_items WHERE deal_id = ?", conn, params=(int(selected_id),))
            conn.close()
            path = generate_pdf(deal_row, items_df)
            with open(path, "rb") as f:
                st.download_button("✅ Download PDF Now", f, file_name=path, mime="application/pdf")
    else:
        st.info("Abhi koi record nahi hai.")

# ---------------- TAB 3: FINANCIAL SHEETS ----------------
with tab3:
    st.title("💳 Financial Sheets")
    st.dataframe(st.session_state.business_df, use_container_width=True)

# ---------------- TAB 4: PERFORMANCE INSIGHTS ----------------
with tab4:
    st.title("📊 Performance Insights")
    if not st.session_state.business_df.empty:
        st.metric("Total Revenue", f"Rs {int(st.session_state.business_df['close_deal'].sum()):,}")
        fig = px.bar(st.session_state.business_df, x='invoice_no', y='close_deal', template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
