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
    pdf.set_draw_color(0, 153, 224) # Blue Border
    pdf.set_font("Arial", "B", 9); pdf.set_fill_color(240, 240, 240)
    pdf.cell(15, 8, "SR #", 1, 0, "C", True); pdf.cell(45, 8, "PRODUCT", 1, 0, "C", True)
    pdf.cell(40, 8, "SPECS", 1, 0, "C", True); pdf.cell(15, 8, "QTY", 1, 0, "C", True)
    pdf.cell(25, 8, "PRICE", 1, 0, "C", True); pdf.cell(25, 8, "TOTAL", 1, 1, "C", True)


def _wrapped_line_count(pdf, text, width):
    """Rough estimate of how many lines a multi_cell(width, ...) call will take,
    used only to size the (optional) Terms & Conditions block for Quotations."""
    total_lines = 0
    for paragraph in text.split("\n"):
        if paragraph.strip() == "":
            total_lines += 1
            continue
        words = paragraph.split(" ")
        current = ""
        for word in words:
            trial = f"{current} {word}".strip()
            if pdf.get_string_width(trial) <= width - 2:
                current = trial
            else:
                total_lines += 1
                current = word
        total_lines += 1
    return max(total_lines, 1)


def generate_pdf(deal, items_df, doc_type="Invoice", terms_text=None):
    pdf = InvoicePDF()
    pdf.add_page()
    blue_color = (0, 153, 224)
    pdf.set_draw_color(*blue_color) # Default draw color set to blue

    # 1. Invoice No & Date
    pdf.set_xy(15, 45)
    pdf.set_font("Arial", "B", 12); pdf.set_text_color(*blue_color)
    pdf.cell(10, 5, "No."); pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 12)
    inv_text = f"{deal['invoice_no']}"
    pdf.set_xy(25, 45); pdf.cell(pdf.get_string_width(inv_text), 5, inv_text)
    pdf.line(25, 50, 25 + pdf.get_string_width(inv_text), 50)

    pdf.set_xy(140, 45); pdf.set_font("Arial", "B", 12); pdf.set_text_color(*blue_color)
    pdf.cell(10, 5, "Date"); pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 12)
    date_val = f"{deal['date']}"
    pdf.set_xy(155, 45); pdf.cell(pdf.get_string_width(date_val), 5, date_val)
    pdf.line(155, 50, 155 + pdf.get_string_width(date_val), 50)

    # 2. Client Name — bold, black underline exactly as long as the name itself
    pdf.set_text_color(0, 0, 0); pdf.set_xy(15, 58); pdf.set_font("Arial", "B", 12)
    pdf.cell(10, 6, "To: ")
    name_x = pdf.get_x()
    client_name = f"{deal['client']}"
    pdf.set_font("Arial", "B", 12)  # bold client name
    pdf.cell(pdf.get_string_width(client_name), 6, client_name)
    pdf.set_draw_color(0, 0, 0)  # black underline just for the client name
    pdf.line(name_x, 64, name_x + pdf.get_string_width(client_name), 64)

    # 3. Table — INVOICE or QUOTATION title depending on what was picked
    pdf.set_xy(0, 70); pdf.set_font("Arial", "B", 16); pdf.cell(210, 8, doc_type.upper(), align="C")

    _draw_item_table_header(pdf, 85)
    pdf.set_font("Arial", "", 9)
    pdf.set_draw_color(0, 153, 224) # Blue border for rows

    for i, item in enumerate(items_df.itertuples(), start=1):
        if pdf.get_y() + 8 > 250:
            pdf.add_page(); _draw_item_table_header(pdf, 45)
            pdf.set_font("Arial", "", 9); pdf.set_draw_color(0, 153, 224)

        pdf.set_x(25)
        pdf.cell(15, 8, str(i), 1, 0, "C")
        pdf.cell(45, 8, str(item.equipment), 1)
        pdf.cell(40, 8, str(item.specs), 1)
        pdf.cell(15, 8, f"{item.quantity:g}", 1, 0, "C")
        pdf.cell(25, 8, f"{item.unit_price:.0f}", 1, 0, "C")
        pdf.cell(25, 8, f"{item.line_total:.0f}", 1, 1, "C")

    # Grand Total
    pdf.set_x(125); pdf.set_font("Arial", "B", 10)
    pdf.cell(40, 8, "Grand Total", 1, 0, "C", True)
    pdf.cell(25, 8, f"{deal['close_deal']:.0f}", 1, 1, "C", True)

    # --- Footer Section Layout (Regards / Account Details / Stamp) ---
    # Invoice keeps the EXACT original fixed layout (y=222 / y=225), untouched.
    # Quotation only: Terms & Conditions is printed right after the table, and the
    # divider/Regards/Account/Stamp block shifts down to make room for it.
    show_terms = doc_type == "Quotation" and terms_text and terms_text.strip()

    if show_terms:
        terms_y = pdf.get_y() + 10
        pdf.set_xy(15, terms_y)
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 5, "Terms & Conditions:", ln=1)
        pdf.set_x(15)
        pdf.set_font("Arial", "", 9)
        pdf.multi_cell(90, 4, terms_text)
        divider_y = pdf.get_y() + 8
        if divider_y + 40 > 255:
            pdf.add_page()
            divider_y = 45
    else:
        divider_y = 222  # original fixed position, unchanged for Invoice

    content_y = divider_y + 3

    # Footer se thoda upar line draw karna
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, divider_y, 200, divider_y)

    # --- Regards & Account Details (Left side) ---
    pdf.set_xy(15, content_y)
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

    # --- Stamp (Right side) ---
    if os.path.exists("stamp.jpg"):
        pdf.image("stamp.jpg", x=140, y=content_y, w=35)

    file_path = f"{doc_type}_{deal['invoice_no']}.pdf"
    pdf.output(file_path)
    return file_path


# --- APP SETUP ---
def init_db():
    conn = sqlite3.connect('enterprise.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS business_deals
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, invoice_no TEXT, client TEXT,
                  equipment TEXT, specs TEXT, actual_price_per_item TEXT, close_deal REAL, actual_cost REAL,
                  paid REAL, remaining REAL, profit REAL, team_member TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS deal_items
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, deal_id INTEGER, equipment TEXT, specs TEXT,
                  quantity REAL, unit_price REAL, unit_actual_cost REAL, line_total REAL, line_actual_cost REAL,
                  FOREIGN KEY(deal_id) REFERENCES business_deals(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS credit_manual
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, total_payment REAL,
                  paid_by_client REAL, remaining_from_client REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS debit_manual
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, total_payment REAL,
                  paid_to_client REAL, remaining_to_be_paid REAL)''')

    # Safety migration: add any columns missing from an older business_deals table on disk.
    existing_cols = [row[1] for row in c.execute("PRAGMA table_info(business_deals)").fetchall()]
    if 'equipment' not in existing_cols:
        c.execute("ALTER TABLE business_deals ADD COLUMN equipment TEXT")
    if 'specs' not in existing_cols:
        c.execute("ALTER TABLE business_deals ADD COLUMN specs TEXT")
    if 'actual_price_per_item' not in existing_cols:
        c.execute("ALTER TABLE business_deals ADD COLUMN actual_price_per_item TEXT")

    conn.commit(); conn.close()


init_db()
st.set_page_config(page_title="Hameez Enterprise Hub", layout="wide")

if 'business_df' not in st.session_state:
    conn = sqlite3.connect('enterprise.db')
    st.session_state.business_df = pd.read_sql("SELECT * FROM business_deals", conn); conn.close()

if 'temp_items' not in st.session_state:
    st.session_state.temp_items = []

if 'credit_manual_df' not in st.session_state or 'debit_manual_df' not in st.session_state:
    conn = sqlite3.connect('enterprise.db')
    st.session_state.credit_manual_df = pd.read_sql("SELECT * FROM credit_manual", conn)
    st.session_state.debit_manual_df = pd.read_sql("SELECT * FROM debit_manual", conn)
    conn.close()

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
        # ---- Without at least one added product, the deal can't be logged ----
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

        # 1 item -> real equipment/specs. >1 items -> comma separated equipment
        # names, specs column just says "Multiple Items".
        if len(items) == 1:
            equipment_display = items[0]['equipment']
            specs_display = items[0]['specs']
        else:
            equipment_display = ", ".join(i['equipment'] for i in items)
            specs_display = "Multiple Items"

        # ---- 1) Actual Price per item, comma separated (same order as equipment) ----
        actual_price_display = ", ".join(f"{i['unit_actual_cost']:.0f}" for i in items)

        conn = sqlite3.connect('enterprise.db')
        cur = conn.cursor()
        # one deal = one row = one invoice_no, with totals summed across all items
        cur.execute("""INSERT INTO business_deals
            (date, invoice_no, client, equipment, specs, actual_price_per_item, close_deal, actual_cost,
             paid, remaining, profit, team_member, status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (datetime.now().strftime("%Y-%m-%d"), inv_no, st.session_state.deal_client, equipment_display,
             specs_display, actual_price_display, close_deal, actual_cost, paid, remaining, profit,
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

        # ---- Add Product button: properly appends the item and clears item fields ----
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
    # ---- 4) invoice_no column dropped from view — 'id' is the unique identifier now ----
    display_df = st.session_state.business_df.drop(columns=['invoice_no'], errors='ignore')
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("🖨️ Generate Invoice / Quotation PDF")
    if not st.session_state.business_df.empty:
        col_a, col_b = st.columns([0.6, 0.4])
        selected_id = col_a.selectbox("Select Deal ID:", st.session_state.business_df['id'].tolist())
        doc_choice = col_b.selectbox("Print as", ["Invoice", "Quotation"])

        terms_text = None
        if doc_choice == "Quotation":
            terms_text = st.text_area(
                "Terms & Conditions (Quotation par print hongi — edit kar sakte hain)",
                "1. 50% advance required, remaining on delivery.\n"
                "2. Prices are valid for 15 days from the quotation date.\n"
                "3. Delivery within 7-10 working days after confirmation."
            )

        # ---- 6) PDF turant generate ho jaati hai selection ke saath — koi alag
        # "Generate" step nahi, sirf ek click (download button) chahiye ----
        conn = sqlite3.connect('enterprise.db')
        deal_row = st.session_state.business_df[st.session_state.business_df['id'] == selected_id].iloc[0]
        items_df = pd.read_sql("SELECT * FROM deal_items WHERE deal_id = ?", conn, params=(int(selected_id),))
        conn.close()

        pdf_path = generate_pdf(deal_row, items_df, doc_type=doc_choice, terms_text=terms_text)
        with open(pdf_path, "rb") as f:
            st.download_button(f"📥 Download {doc_choice} PDF", f, file_name=pdf_path, mime="application/pdf")
    else:
        st.info("Abhi koi record nahi hai.")

# ---------------- TAB 3: CREDIT / DEBIT SHEETS ----------------
with tab3:
    st.title("💳 Credit / Debit Sheets")
    st.caption(
        "Deals ke records se yeh sheets khud-ba-khud update hoti hain. Agar client ne poora ya "
        "kam payment kiya ho to woh deal Credit Sheet mein jaati hai (client ne humein dena hai). "
        "Agar client ne zyada payment kar di ho (overpaid) to woh Debit Sheet mein jaati hai "
        "(humein client ko wapas dena hai). Neeche se manual entries (jinke paise dene/lene hain, "
        "deals se bahar) bhi add kar sakte hain."
    )

    def _add_credit_cb():
        name = st.session_state.credit_new_client
        if name and name.strip():
            total_payment = st.session_state.credit_new_total
            paid_by = st.session_state.credit_new_paid
            remaining = total_payment - paid_by
            conn = sqlite3.connect('enterprise.db')
            conn.execute(
                "INSERT INTO credit_manual (client, total_payment, paid_by_client, remaining_from_client) VALUES (?,?,?,?)",
                (name, total_payment, paid_by, remaining))
            conn.commit()
            st.session_state.credit_manual_df = pd.read_sql("SELECT * FROM credit_manual", conn)
            conn.close()
            st.session_state.credit_new_client = ""
            st.session_state.credit_new_total = 0.0
            st.session_state.credit_new_paid = 0.0
            st.session_state.credit_add_warning = False
        else:
            st.session_state.credit_add_warning = True

    def _add_debit_cb():
        name = st.session_state.debit_new_client
        if name and name.strip():
            total_payment = st.session_state.debit_new_total
            paid_to = st.session_state.debit_new_paid
            remaining = total_payment - paid_to
            conn = sqlite3.connect('enterprise.db')
            conn.execute(
                "INSERT INTO debit_manual (client, total_payment, paid_to_client, remaining_to_be_paid) VALUES (?,?,?,?)",
                (name, total_payment, paid_to, remaining))
            conn.commit()
            st.session_state.debit_manual_df = pd.read_sql("SELECT * FROM debit_manual", conn)
            conn.close()
            st.session_state.debit_new_client = ""
            st.session_state.debit_new_total = 0.0
            st.session_state.debit_new_paid = 0.0
            st.session_state.debit_add_warning = False
        else:
            st.session_state.debit_add_warning = True

    def _save_credit_edits_cb():
        edited = st.session_state.credit_editor_data
        conn = sqlite3.connect('enterprise.db')
        conn.execute("DELETE FROM credit_manual")
        for row in edited.to_dict("records"):
            if str(row.get('client', '')).strip():
                total_payment = row.get('total_payment', 0) or 0
                paid_by = row.get('paid_by_client', 0) or 0
                conn.execute(
                    "INSERT INTO credit_manual (client, total_payment, paid_by_client, remaining_from_client) VALUES (?,?,?,?)",
                    (row['client'], total_payment, paid_by, total_payment - paid_by))
        conn.commit()
        st.session_state.credit_manual_df = pd.read_sql("SELECT * FROM credit_manual", conn)
        conn.close()

    def _save_debit_edits_cb():
        edited = st.session_state.debit_editor_data
        conn = sqlite3.connect('enterprise.db')
        conn.execute("DELETE FROM debit_manual")
        for row in edited.to_dict("records"):
            if str(row.get('client', '')).strip():
                total_payment = row.get('total_payment', 0) or 0
                paid_to = row.get('paid_to_client', 0) or 0
                conn.execute(
                    "INSERT INTO debit_manual (client, total_payment, paid_to_client, remaining_to_be_paid) VALUES (?,?,?,?)",
                    (row['client'], total_payment, paid_to, total_payment - paid_to))
        conn.commit()
        st.session_state.debit_manual_df = pd.read_sql("SELECT * FROM debit_manual", conn)
        conn.close()

    deals = st.session_state.business_df
    credit_tab, debit_tab = st.tabs(["💰 Credit Sheet (Client hume dega)", "💸 Debit Sheet (Hum client ko dengay)"])

    # ---------------- CREDIT SHEET ----------------
    with credit_tab:
        auto_credit = deals[deals['remaining'] >= 0].copy() if not deals.empty else deals
        auto_credit_view = pd.DataFrame({
            "Client Name": auto_credit['client'],
            "Id No": "D-" + auto_credit['id'].astype(str),
            "Total Payment": auto_credit['close_deal'],
            "Paid by Client": auto_credit['paid'],
            "Remaining from Client": auto_credit['remaining'],
        }) if not auto_credit.empty else pd.DataFrame(
            columns=["Client Name", "Id No", "Total Payment", "Paid by Client", "Remaining from Client"])

        manual_c = st.session_state.credit_manual_df
        manual_c_view = pd.DataFrame({
            "Client Name": manual_c['client'],
            "Id No": "C-" + manual_c['id'].astype(str),
            "Total Payment": manual_c['total_payment'],
            "Paid by Client": manual_c['paid_by_client'],
            "Remaining from Client": manual_c['remaining_from_client'],
        }) if not manual_c.empty else pd.DataFrame(
            columns=["Client Name", "Id No", "Total Payment", "Paid by Client", "Remaining from Client"])

        st.subheader("📋 Full Credit Sheet")
        st.dataframe(pd.concat([auto_credit_view, manual_c_view], ignore_index=True),
                     use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("➕ Add Manual Entry (deals se bahar, jinse paise lene hain)")
        cc1, cc2, cc3 = st.columns(3)
        cc1.text_input("Client Name", key="credit_new_client")
        cc2.number_input("Total Payment", min_value=0.0, format="%g", key="credit_new_total")
        cc3.number_input("Paid by Client", min_value=0.0, format="%g", key="credit_new_paid")
        st.button("➕ Add to Credit Sheet", on_click=_add_credit_cb, key="add_credit_btn")
        if st.session_state.get("credit_add_warning"):
            st.warning("Client Name likhna zaroori hai.")

        if not st.session_state.credit_manual_df.empty:
            st.write("**Manual Entries (editable)**")
            edited_credit = st.data_editor(
                st.session_state.credit_manual_df.drop(columns=['id']),
                use_container_width=True, hide_index=True, num_rows="dynamic", key="credit_editor_data")
            st.button("💾 Save Credit Changes", on_click=_save_credit_edits_cb, key="save_credit_btn")

    # ---------------- DEBIT SHEET ----------------
    with debit_tab:
        auto_debit = deals[deals['remaining'] < 0].copy() if not deals.empty else deals
        auto_debit_view = pd.DataFrame({
            "Client Name": auto_debit['client'],
            "Id No": "D-" + auto_debit['id'].astype(str),
            "Total Payment": auto_debit['close_deal'],
            "Paid to Client": 0,
            "Remaining to be paid": auto_debit['remaining'].abs(),
        }) if not auto_debit.empty else pd.DataFrame(
            columns=["Client Name", "Id No", "Total Payment", "Paid to Client", "Remaining to be paid"])

        manual_d = st.session_state.debit_manual_df
        manual_d_view = pd.DataFrame({
            "Client Name": manual_d['client'],
            "Id No": "C-" + manual_d['id'].astype(str),
            "Total Payment": manual_d['total_payment'],
            "Paid to Client": manual_d['paid_to_client'],
            "Remaining to be paid": manual_d['remaining_to_be_paid'],
        }) if not manual_d.empty else pd.DataFrame(
            columns=["Client Name", "Id No", "Total Payment", "Paid to Client", "Remaining to be paid"])

        st.subheader("📋 Full Debit Sheet")
        st.dataframe(pd.concat([auto_debit_view, manual_d_view], ignore_index=True),
                     use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("➕ Add Manual Entry (deals se bahar, jinko paise dene hain)")
        dc1, dc2, dc3 = st.columns(3)
        dc1.text_input("Client Name", key="debit_new_client")
        dc2.number_input("Total Payment", min_value=0.0, format="%g", key="debit_new_total")
        dc3.number_input("Paid to Client", min_value=0.0, format="%g", key="debit_new_paid")
        st.button("➕ Add to Debit Sheet", on_click=_add_debit_cb, key="add_debit_btn")
        if st.session_state.get("debit_add_warning"):
            st.warning("Client Name likhna zaroori hai.")

        if not st.session_state.debit_manual_df.empty:
            st.write("**Manual Entries (editable)**")
            edited_debit = st.data_editor(
                st.session_state.debit_manual_df.drop(columns=['id']),
                use_container_width=True, hide_index=True, num_rows="dynamic", key="debit_editor_data")
            st.button("💾 Save Debit Changes", on_click=_save_debit_edits_cb, key="save_debit_btn")

# ---------------- TAB 4: PERFORMANCE INSIGHTS ----------------
with tab4:
    st.title("📊 Performance Insights")
    if not st.session_state.business_df.empty:
        st.metric("Total Revenue", f"Rs {int(st.session_state.business_df['close_deal'].sum()):,}")
        fig = px.bar(st.session_state.business_df, x='id', y='close_deal', template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
