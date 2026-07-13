import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import os
import plotly.express as px

# --- PDF GENERATOR CLASS (Letterhead / header / footer design UNCHANGED) ---
class InvoicePDF(FPDF):
    def header(self):
        self.set_fill_color(0, 51, 102); self.rect(10, 8, 22, 8, "F")
        self.set_fill_color(0, 153, 224); self.rect(35, 8, 165, 8, "F")
        if os.path.exists("lo.png"): self.image("lo.png", x=10, y=18, w=25)
        self.set_xy(40, 20); self.set_font("Arial", "B", 20); self.set_text_color(20, 40, 80)
        self.cell(0, 10, "Badar Diagnostics & Medical Equipments")

    def footer(self):
        self.set_fill_color(0, 51, 102); self.rect(10, 260, 190, 15, "F")
        self.set_fill_color(0, 153, 224); self.rect(10, 275, 190, 8, "F")
        self.set_y(262); self.set_text_color(255, 255, 255); self.set_font("Arial", "", 7)
        self.multi_cell(0, 3.5, "Lahore Office: D Block Nawab Town, Lahore   |   Okara Office: Adjacent Ibn-e-Sina Lab, Opposite DHQ, Okara\nPindi Office: Commercial Market, Rawalpindi   |   Bahawalpur Office: Model Town C, Bahawalpur", align="C")
        self.set_y(276); self.set_font("Arial", "B", 8)
        self.cell(0, 4, " 0300-7303020, 0334-7303020      E-mail: munir.badar1@gmail.com", align="C")


def _draw_item_table_header(pdf, y):
    pdf.set_xy(25, y)
    pdf.set_font("Arial", "B", 9); pdf.set_fill_color(240, 240, 240)
    pdf.cell(15, 8, "SR #", 1, 0, "C", True); pdf.cell(45, 8, "PRODUCT", 1, 0, "C", True)
    pdf.cell(40, 8, "SPECS", 1, 0, "C", True); pdf.cell(15, 8, "QTY", 1, 0, "C", True)
    pdf.cell(25, 8, "PRICE", 1, 0, "C", True); pdf.cell(25, 8, "TOTAL", 1, 1, "C", True)


def generate_pdf(deal, items_df):
    """deal = single row from business_deals, items_df = every product belonging to that deal.
    Design (No./Date, To:, table, Grand Total, Regards/Account Details/Stamp) is the exact
    quotation/invoice design provided. Only change: the item table now loops over multiple
    products, and the Regards/Account/Stamp block sits dynamically right below the table
    (with auto page-break) instead of a fixed y, since table height now varies with item count."""
    pdf = InvoicePDF()
    pdf.add_page()
    blue_color = (0, 153, 224)

    # 1. Invoice No. Section
    pdf.set_xy(15, 45)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(*blue_color)
    pdf.cell(10, 5, "No.")

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 12)
    inv_text = f"{deal['invoice_no']}"
    pdf.set_xy(25, 45)
    pdf.cell(pdf.get_string_width(inv_text), 5, inv_text)

    pdf.set_draw_color(*blue_color)
    pdf.line(25, 50, 25 + pdf.get_string_width(inv_text), 50)

    # 2. Date Section (Gap ke sath)
    date_label = "Date"
    date_val = f"{deal['date']}"

    pdf.set_xy(140, 45)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(*blue_color)
    pdf.cell(10, 5, date_label)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 12)
    date_x = 140 + pdf.get_string_width(date_label) + 5
    pdf.set_xy(date_x, 45)
    pdf.cell(pdf.get_string_width(date_val), 5, date_val)

    pdf.line(date_x, 50, date_x + pdf.get_string_width(date_val), 50)

    # 3. Client Name (Underline ke sath)
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(15, 58)
    pdf.set_font("Arial", "B", 12)
    client_label = "To: "
    client_name = f"{deal['client']}"

    pdf.cell(pdf.get_string_width(client_label), 6, client_label)
    pdf.set_font("Arial", "", 12)
    pdf.cell(pdf.get_string_width(client_name), 6, client_name)

    pdf.set_draw_color(0, 0, 0)
    pdf.line(15 + pdf.get_string_width(client_label), 64,
             15 + pdf.get_string_width(client_label) + pdf.get_string_width(client_name), 64)

    # Title
    pdf.set_xy(0, 70)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(210, 8, "INVOICE", align="C")

    # Table Header + multi-item rows (auto page-break, header repeats on new page)
    _draw_item_table_header(pdf, 85)
    pdf.set_font("Arial", "", 9)

    for i, item in enumerate(items_df.itertuples(), start=1):
        if pdf.get_y() + 8 > 250:
            pdf.add_page()
            _draw_item_table_header(pdf, 45)
            pdf.set_font("Arial", "", 9)

        pdf.set_x(25)
        pdf.cell(15, 8, str(i), 1, 0, "C")
        pdf.cell(45, 8, str(item.equipment), 1)
        pdf.cell(40, 8, str(item.specs), 1)
        pdf.cell(15, 8, f"{item.quantity:g}", 1, 0, "C")
        pdf.cell(25, 8, f"{item.unit_price:.0f}", 1, 0, "C")
        pdf.cell(25, 8, f"{item.line_total:.0f}", 1, 1, "C")

    if pdf.get_y() + 16 > 250:
        pdf.add_page()
        pdf.set_y(45)

    # Grand Total
    pdf.set_x(125); pdf.set_font("Arial", "B", 10)
    pdf.cell(40, 8, "Grand Total", 1, 0, "C", True)
    pdf.cell(25, 8, f"{deal['close_deal']:.0f}", 1, 1, "C", True)

    # --- Footer Section Layout (Regards / Account Details / Stamp) ---
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
                  equipment TEXT, specs TEXT, close_deal REAL, actual_cost REAL, paid REAL,
                  remaining REAL, profit REAL, team_member TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS deal_items
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, deal_id INTEGER, equipment TEXT, specs TEXT,
                  quantity REAL, unit_price REAL, unit_actual_cost REAL, line_total REAL, line_actual_cost REAL,
                  FOREIGN KEY(deal_id) REFERENCES business_deals(id))''')

    # Safety migration: if an older business_deals table (without equipment/specs) already
    # exists on disk, add the missing columns instead of breaking.
    existing_cols = [row[1] for row in c.execute("PRAGMA table_info(business_deals)").fetchall()]
    if 'equipment' not in existing_cols:
        c.execute("ALTER TABLE business_deals ADD COLUMN equipment TEXT")
    if 'specs' not in existing_cols:
        c.execute("ALTER TABLE business_deals ADD COLUMN specs TEXT")

    conn.commit(); conn.close()


init_db()
st.set_page_config(page_title="Hameez Enterprise Hub", layout="wide")

if 'business_df' not in st.session_state:
    conn = sqlite3.connect('enterprise.db')
    st.session_state.business_df = pd.read_sql("SELECT * FROM business_deals", conn); conn.close()

if 'temp_items' not in st.session_state:
    st.session_state.temp_items = []

tab1, tab2, tab3, tab4 = st.tabs(["🏠 Home Finance", "💼 Business Deals", "💳 Credit/Debit Sheets", "📊 Analytics"])

# ---------------- TAB 2: BUSINESS DEALS ----------------
with tab2:
    st.title("💼 Business Deals")

    # ---- callback helpers ----
    # IMPORTANT: widget-tied session_state keys can only be reset INSIDE a callback
    # (on_click), never in the normal script body after that widget has already
    # rendered in the same run — that's what was causing the StreamlitAPIException.

    def _add_item_cb():
        name = st.session_state.item_name_input
        if name and name.strip():
            qty = st.session_state.item_qty_input
            price = st.session_state.item_price_input
            cost = st.session_state.item_cost_input
            st.session_state.temp_items.append({
                'equipment': name,
                'specs': st.session_state.item_specs_input,
                'quantity': qty,
                'unit_price': price,
                'unit_actual_cost': cost,
                'line_total': qty * price,
                'line_actual_cost': qty * cost,
            })
            # reset only the product fields so client/team/paid stay filled
            st.session_state.item_name_input = ""
            st.session_state.item_specs_input = ""
            st.session_state.item_qty_input = 1
            st.session_state.item_price_input = 0.0
            st.session_state.item_cost_input = 0.0
            st.session_state.add_item_warning = False
        else:
            st.session_state.add_item_warning = True

    def _remove_item_cb(idx):
        if 0 <= idx < len(st.session_state.temp_items):
            st.session_state.temp_items.pop(idx)

    def _log_deal_cb():
        # ---- 2) Without at least one added product, the deal can't be logged ----
        if not st.session_state.temp_items:
            st.session_state.deal_message = ("error", "Pehle kam az kam ek product add karein.")
            return
        if not st.session_state.deal_client.strip():
            st.session_state.deal_message = ("error", "Client Name zaroori hai.")
            return

        items = st.session_state.temp_items
        close_deal = sum(i['line_total'] for i in items)
        actual_cost = sum(i['line_actual_cost'] for i in items)
        paid = st.session_state.deal_paid
        remaining = close_deal - paid
        profit = close_deal - actual_cost
        status = "Paid" if remaining <= 0 else "Pending"
        inv_no = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # ---- 5) 1 item -> real equipment/specs. >1 items -> comma separated
        # equipment names, specs column just says "Multiple Items" ----
        if len(items) == 1:
            equipment_display = items[0]['equipment']
            specs_display = items[0]['specs']
        else:
            equipment_display = ", ".join(i['equipment'] for i in items)
            specs_display = "Multiple Items"

        conn = sqlite3.connect('enterprise.db')
        cur = conn.cursor()
        # ---- 4) one deal = one row = one invoice_no, with totals summed across
        # all items (close_deal, actual_cost, paid, remaining, profit) ----
        cur.execute("""INSERT INTO business_deals
            (date, invoice_no, client, equipment, specs, close_deal, actual_cost,
             paid, remaining, profit, team_member, status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (datetime.now().strftime("%Y-%m-%d"), inv_no, st.session_state.deal_client, equipment_display,
             specs_display, close_deal, actual_cost, paid, remaining, profit,
             st.session_state.deal_team_member, status))
        deal_id = cur.lastrowid

        for item in items:
            cur.execute("""INSERT INTO deal_items
                (deal_id, equipment, specs, quantity, unit_price, unit_actual_cost, line_total, line_actual_cost)
                VALUES (?,?,?,?,?,?,?,?)""",
                (deal_id, item['equipment'], item['specs'], item['quantity'], item['unit_price'],
                 item['unit_actual_cost'], item['line_total'], item['line_actual_cost']))

        conn.commit()
        st.session_state.business_df = pd.read_sql("SELECT * FROM business_deals", conn)
        conn.close()

        st.session_state.temp_items = []
        st.session_state.deal_client = ""
        st.session_state.deal_team_member = ""
        st.session_state.deal_paid = 0.0
        st.session_state.deal_message = ("success", f"Deal {inv_no} save ho gayi!")

    with st.container(border=True):
        c1, c2 = st.columns(2)
        client = c1.text_input("Client Name/Hospital", key="deal_client")
        team_member = c2.text_input("Team Member (Optional)", key="deal_team_member")

        c3, c4 = st.columns(2)
        item_name = c3.text_input("Equipment Name", key="item_name_input")
        item_specs = c4.text_input("Specs", key="item_specs_input")

        c5, c6, c7 = st.columns(3)
        item_qty = c5.number_input("Qty", min_value=1, format="%g", key="item_qty_input")
        item_price = c6.number_input("Unit Price", min_value=0.0, format="%g", key="item_price_input")
        item_cost = c7.number_input("Actual Cost", min_value=0.0, format="%g", key="item_cost_input")

        paid = st.number_input("Payment sent by Client", min_value=0.0, format="%g", key="deal_paid")

        # ---- 1) Add Product button: properly appends the item and clears item fields ----
        st.button("➕ Add to List", use_container_width=True, on_click=_add_item_cb)
        if st.session_state.get("add_item_warning"):
            st.warning("Equipment Name likhna zaroori hai.")

        # show what's queued so far, so you know what will go into the invoice
        if st.session_state.temp_items:
            st.write("**Added Items:**")
            for idx, item in enumerate(st.session_state.temp_items):
                ic1, ic2, ic3, ic4, ic5, ic6 = st.columns([2, 2, 1, 1, 1, 0.6])
                ic1.write(item['equipment']); ic2.write(item['specs'])
                ic3.write(f"{item['quantity']:g}"); ic4.write(f"{item['unit_price']:.0f}")
                ic5.write(f"{item['line_total']:.0f}")
                ic6.button("🗑️", key=f"del_item_{idx}", on_click=_remove_item_cb, args=(idx,))
            st.caption(f"Running Total: Rs {sum(i['line_total'] for i in st.session_state.temp_items):,.0f}")

    with st.form("deal_form", clear_on_submit=True):
        st.form_submit_button("✅ Log Deal", use_container_width=True, on_click=_log_deal_cb)

    if st.session_state.get("deal_message"):
        level, text = st.session_state.deal_message
        getattr(st, level)(text)
        st.session_state.deal_message = None

    st.divider()
    st.subheader("📋 Records")
    # ---- 3) equipment & specs now their own columns, visible here automatically ----
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
