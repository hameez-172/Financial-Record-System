import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from fpdf import FPDF
import os
import plotly.express as px

# =========================================================================
# DISPLAY / EXPORT COLUMN CONFIG
# (kept in one place so Records / Credit / Debit / Expense sheets all use
#  the same column order + headers everywhere: on-screen table, editor,
#  CSV export and PDF export)
# =========================================================================

# NOTE: actual_price_per_item now sits AFTER actual_cost (point 6)
RECORD_DISPLAY_COLUMNS = ['id', 'date', 'client', 'equipment', 'specs', 'close_deal',
                          'actual_cost', 'actual_price_per_item', 'paid', 'remaining',
                          'profit', 'team_member', 'status']
RECORD_DISPLAY_HEADERS = ['No.', 'Date', 'Client', 'Equipment', 'Specs', 'Close Deal',
                           'Actual Cost', 'Actual Price/Item', 'Paid', 'Remaining',
                           'Profit', 'Team Member', 'Status']
RECORD_COL_WIDTHS = [10, 18, 30, 30, 26, 20, 20, 24, 18, 20, 18, 22, 21]  # sums to 277mm (A4 landscape usable width)

CREDIT_HEADERS = ["Client Name", "Id No", "Total Payment", "Paid by Client", "Remaining from Client"]
CREDIT_COL_WIDTHS = [60, 35, 60, 60, 62]  # sums to 277mm

DEBIT_HEADERS = ["Client Name", "Id No", "Total Payment", "Paid to Client", "Remaining to be paid"]
DEBIT_COL_WIDTHS = [60, 35, 60, 60, 62]  # sums to 277mm

EXPENSE_HEADERS = ["Description", "Amount"]
EXPENSE_COL_WIDTHS = [130, 60]  # sums to 190mm (A4 portrait usable width) -- point 4: only 2 columns


# --- PDF GENERATOR CLASS (Letterhead / header / footer design UNCHANGED in spirit,
#     just made width/height-aware so the same letterhead works in both
#     portrait and landscape pages) ---
class InvoicePDF(FPDF):
    def header(self):
        self.set_fill_color(0, 51, 102); self.rect(10, 8, 22, 8, "F")
        blue_w = self.w - 45
        self.set_fill_color(0, 153, 224); self.rect(35, 8, blue_w, 8, "F")
        if os.path.exists("lo.png"): self.image("lo.png", x=10, y=18, w=25)
        self.set_xy(40, 20); self.set_font("Arial", "B", 20); self.set_text_color(20, 40, 80)
        self.cell(0, 10, "Badar Diagnostics & Medical Equipments")

    def footer(self):
        rect_w = self.w - 20
        navy_y = self.h - 37
        blue_y = self.h - 22
        self.set_fill_color(0, 51, 102); self.rect(10, navy_y, rect_w, 15, "F")
        self.set_fill_color(0, 153, 224); self.rect(10, blue_y, rect_w, 8, "F")
        self.set_y(self.h - 35); self.set_text_color(255, 255, 255); self.set_font("Arial", "", 7)
        self.multi_cell(0, 3.5, "Lahore Office: D Block Nawab Town, Lahore   |   Okara Office: Adjacent Ibn-e-Sina Lab, Opposite DHQ, Okara\nPindi Office: Commercial Market, Rawalpindi   |   Bahawalpur Office: Model Town C, Bahawalpur", align="C")
        self.set_y(self.h - 21); self.set_font("Arial", "B", 8)
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
    """Generates Invoice / Quotation / Delivery Challan (always portrait, single record).
    Delivery Challan: same layout as Invoice but PRICE/TOTAL cells are left blank
    (not even 0) and no Grand Total is printed."""
    pdf = InvoicePDF()
    pdf.add_page()
    blue_color = (0, 153, 224)
    pdf.set_draw_color(*blue_color) # Default draw color set to blue

    is_challan = (doc_type == "Delivery Challan")

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

    # 3. Table — INVOICE / QUOTATION / DELIVERY CHALLAN title depending on what was picked
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
        if is_challan:
            # Delivery Challan: price/total left completely blank, not even 0
            pdf.cell(25, 8, "", 1, 0, "C")
            pdf.cell(25, 8, "", 1, 1, "C")
        else:
            pdf.cell(25, 8, f"{item.unit_price:.0f}", 1, 0, "C")
            pdf.cell(25, 8, f"{item.line_total:.0f}", 1, 1, "C")

    # Grand Total (skipped entirely for Delivery Challan since there's no pricing)
    # Point 5: if the item table ran all the way down to the bottom, make sure the
    # Grand Total row itself still has room -- otherwise start a fresh page first
    # instead of letting it collide with the footer band.
    if pdf.get_y() + 20 > 250:
        pdf.add_page()

    if not is_challan:
        pdf.set_x(125); pdf.set_font("Arial", "B", 10)
        pdf.cell(40, 8, "Grand Total", 1, 0, "C", True)
        pdf.cell(25, 8, f"{deal['close_deal']:.0f}", 1, 1, "C", True)

    # --- Footer Section Layout (Regards / Account Details / Stamp) ---
    # Point 2: Quotation's account details/stamp now sit at the SAME fixed level as
    # Invoice / Delivery Challan (just above the footer band), instead of floating
    # right after a short Terms & Conditions block.
    # Point 5: if the Terms text (or a long item table) would run down into that
    # fixed zone, jump to a new page first instead of overlapping the logo/account
    # details/stamp.
    show_terms = doc_type == "Quotation" and terms_text and terms_text.strip()
    divider_y = 222  # fixed position, same level as Invoice / Delivery Challan

    if show_terms:
        if pdf.get_y() + 10 > 195:
            pdf.add_page()
        terms_y = pdf.get_y() + 10
        pdf.set_xy(15, terms_y)
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 5, "Terms & Conditions:", ln=1)
        pdf.set_x(15)
        pdf.set_font("Arial", "", 9)
        pdf.multi_cell(90, 4, terms_text)

    # Safety net: whatever was just printed (table / grand total / terms) must not
    # run into the fixed divider_y zone -- if it does, move to a new page so the
    # account details/stamp never overlap it.
    if pdf.get_y() + 10 > divider_y:
        pdf.add_page()

    content_y = divider_y + 3

    # Footer se thoda upar line draw karna
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, divider_y, 200, divider_y)

    # --- Regards & Account Details (Left side) ---
    # Stamp + Account Details appear on Invoice / Quotation / Delivery Challan only
    # (never on the Records / Credit / Debit / Expense sheet exports).
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

    file_path = f"{doc_type.replace(' ', '_')}_{deal['invoice_no']}.pdf"
    pdf.output(file_path)
    return file_path


# =========================================================================
# GENERIC SHEET EXPORT (Records / Credit Sheet / Debit Sheet / Expense Sheet)
# Records / Credit / Debit -> landscape, no stamp / account details, title
# in the usual title-slot says "Records" / "Credit Sheet" / "Debit Sheet".
# Expense Sheet -> portrait, only 2 columns (Description, Amount), no
# stamp / account details, title says "Expense Sheet".
# =========================================================================

def _draw_sheet_table_header(pdf, headers, col_widths, y, start_x=10):
    pdf.set_xy(start_x, y)
    pdf.set_draw_color(0, 153, 224)
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_text_color(0, 0, 0)
    for h, w in zip(headers, col_widths):
        pdf.cell(w, 8, str(h), 1, 0, "C", True)


def generate_sheet_pdf(df, headers, col_widths, title, filename_prefix, orientation="L"):
    pdf = InvoicePDF(orientation=orientation)
    pdf.add_page()
    start_x = 10
    title_y = 30 if orientation == "L" else 45
    pdf.set_xy(0, title_y)
    pdf.set_font("Arial", "B", 16); pdf.set_text_color(0, 0, 0)
    pdf.cell(pdf.w, 8, title.upper(), align="C")

    table_y = title_y + 14
    _draw_sheet_table_header(pdf, headers, col_widths, table_y, start_x)
    pdf.set_font("Arial", "", 8); pdf.set_text_color(0, 0, 0); pdf.set_draw_color(0, 153, 224)

    row_h = 7
    y = table_y + 8
    bottom_limit = pdf.h - 45  # leave room for the letterhead footer band (point 5)

    for _, row in df.iterrows():
        if y + row_h > bottom_limit:
            pdf.add_page()
            y = title_y
            _draw_sheet_table_header(pdf, headers, col_widths, y, start_x)
            pdf.set_font("Arial", "", 8); pdf.set_draw_color(0, 153, 224)
            y += 8
        pdf.set_xy(start_x, y)
        for val, w in zip(row.tolist(), col_widths):
            text = "" if pd.isna(val) else str(val)
            pdf.cell(w, row_h, text, 1, 0, "C")
        y += row_h

    path = f"{filename_prefix}.pdf"
    pdf.output(path)
    return path


def _df_to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8-sig")


def _apply_date_filter(df, date_col, start, end):
    """Point 3: filter any sheet's dataframe down to a [start, end] date range
    (inclusive), based on date_col. Rows whose date can't be parsed, or where no
    date_col exists, are left as-is (untouched) rather than dropped."""
    if df is None or df.empty or date_col not in df.columns or start is None or end is None:
        return df
    parsed = pd.to_datetime(df[date_col], errors='coerce')
    mask = (parsed.dt.date >= start) & (parsed.dt.date <= end) | parsed.isna()
    return df[mask]


# --- APP SETUP ---
def init_db():
    conn = sqlite3.connect('enterprise.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS business_deals
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, invoice_no TEXT, client TEXT,
                  equipment TEXT, specs TEXT, close_deal REAL, actual_cost REAL, actual_price_per_item TEXT,
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
    c.execute('''CREATE TABLE IF NOT EXISTS daily_expenses
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, category TEXT,
                  description TEXT, amount REAL)''')

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

if 'expense_df' not in st.session_state:
    conn = sqlite3.connect('enterprise.db')
    st.session_state.expense_df = pd.read_sql("SELECT * FROM daily_expenses", conn)
    conn.close()

tab1, tab2, tab3, tab4 = st.tabs(["🏠 Home Finance", "💼 Business Deals", "💳 Credit/Debit/Expense Sheets", "📊 Analytics"])

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
            (date, invoice_no, client, equipment, specs, close_deal, actual_cost, actual_price_per_item,
             paid, remaining, profit, team_member, status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (datetime.now().strftime("%Y-%m-%d"), inv_no, st.session_state.deal_client, equipment_display,
             specs_display, close_deal, actual_cost, actual_price_display, paid, remaining, profit,
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

    def _save_records_edits(edited):
        # Records (Business Deals) editable table — recompute remaining/profit/status
        # from the edited numbers so the sheet always stays internally consistent.
        # NOTE: `edited` must be the DataFrame RETURNED by st.data_editor(), not
        # st.session_state[key] — for data_editor, session_state[key] only holds
        # a raw {edited_rows, added_rows, deleted_rows} dict, not a merged DataFrame.
        #
        # Point 1: Records / Credit / Debit sheets are linked (Credit/Debit are
        # derived live from st.session_state.business_df). If the user directly
        # edits "remaining" down to 0 (instead of editing "paid"), that edit is
        # now honored — "paid" is back-derived from it — so the row's status
        # flips to "Paid" and it shows correctly (with remaining = 0) wherever
        # Credit/Debit sheets pull from this table.
        conn = sqlite3.connect('enterprise.db')
        cur = conn.cursor()
        for row in edited.to_dict("records"):
            close_deal = row.get('close_deal', 0) or 0
            actual_cost = row.get('actual_cost', 0) or 0
            paid = row.get('paid', 0) or 0
            remaining_edited = row.get('remaining', None)
            if remaining_edited is not None and remaining_edited != (close_deal - paid):
                # user edited "remaining" directly -> treat it as the source of truth
                remaining = remaining_edited
                paid = close_deal - remaining
            else:
                remaining = close_deal - paid
            profit = close_deal - actual_cost
            status = "Paid" if remaining <= 0 else "Pending"
            cur.execute("""UPDATE business_deals SET date=?, client=?, equipment=?, specs=?,
                           close_deal=?, actual_cost=?, actual_price_per_item=?, paid=?, remaining=?,
                           profit=?, team_member=?, status=? WHERE id=?""",
                        (row.get('date'), row.get('client'), row.get('equipment'), row.get('specs'),
                         close_deal, actual_cost, row.get('actual_price_per_item'), paid, remaining,
                         profit, row.get('team_member'), status, row.get('id')))
        conn.commit()
        st.session_state.business_df = pd.read_sql("SELECT * FROM business_deals", conn)
        conn.close()

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

    # ---- Date filter for Records (point 3) ----
    _all_dates = pd.to_datetime(st.session_state.business_df['date'], errors='coerce') \
        if not st.session_state.business_df.empty else pd.Series([], dtype='datetime64[ns]')
    _default_from = _all_dates.min().date() if not _all_dates.empty and _all_dates.notna().any() else date.today()
    _default_to = _all_dates.max().date() if not _all_dates.empty and _all_dates.notna().any() else date.today()
    rf1, rf2 = st.columns(2)
    records_from = rf1.date_input("From", value=_default_from, key="records_filter_from")
    records_to = rf2.date_input("To", value=_default_to, key="records_filter_to")

    # ---- Build the display dataframe in the fixed column order (point 6) ----
    display_df = st.session_state.business_df.copy()
    for col in RECORD_DISPLAY_COLUMNS:
        if col not in display_df.columns:
            display_df[col] = None
    display_df = display_df[RECORD_DISPLAY_COLUMNS]
    display_df = _apply_date_filter(display_df, 'date', records_from, records_to)

    # ---- Editable records sheet (point 7) ----
    edited_records = st.data_editor(
        display_df, use_container_width=True, hide_index=True, num_rows="fixed",
        disabled=["id"], key="records_editor_data"
    )
    if st.button("💾 Save Records Changes", key="save_records_btn"):
        _save_records_edits(edited_records)
        st.success("Records update ho gaye!")

    # ---- Records CSV / PDF export (point 3 & 5: landscape, "Records" heading, no stamp/account) ----
    if not display_df.empty:
        export_df = display_df.sort_values('id', ascending=False)  # most recent first
        export_df_named = export_df.rename(columns=dict(zip(RECORD_DISPLAY_COLUMNS, RECORD_DISPLAY_HEADERS)))
        rc1, rc2 = st.columns(2)
        rc1.download_button("⬇️ Records CSV", data=_df_to_csv_bytes(export_df_named),
                             file_name="records.csv", mime="text/csv", key="records_csv_btn")
        records_pdf_path = generate_sheet_pdf(export_df, RECORD_DISPLAY_HEADERS, RECORD_COL_WIDTHS,
                                               "Records", "records_sheet", orientation="L")
        with open(records_pdf_path, "rb") as f:
            rc2.download_button("⬇️ Records PDF", data=f, file_name="records.pdf",
                                 mime="application/pdf", key="records_pdf_btn")

    st.divider()
    st.subheader("🖨️ Generate Invoice / Quotation / Delivery Challan")
    if not st.session_state.business_df.empty:
        col_a, col_b = st.columns([0.6, 0.4])
        selected_id = col_a.selectbox("Select Deal ID:", st.session_state.business_df['id'].tolist())
        doc_choice = col_b.selectbox("Print as", ["Invoice", "Quotation", "Delivery Challan"])

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

# ---------------- TAB 3: CREDIT / DEBIT / EXPENSE SHEETS ----------------
with tab3:
    st.title("💳 Credit / Debit / Expense Sheets")
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

    def _save_credit_edits(edited):
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

    def _save_debit_edits(edited):
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

    def _add_expense_cb():
        category = st.session_state.expense_category_input
        description = (st.session_state.expense_desc_manual_input
                        if category == "Others" else category)
        if not description or not str(description).strip():
            st.session_state.expense_add_warning = True
            return
        amount = st.session_state.expense_amount_input
        exp_date = st.session_state.expense_date_input
        conn = sqlite3.connect('enterprise.db')
        conn.execute(
            "INSERT INTO daily_expenses (date, category, description, amount) VALUES (?,?,?,?)",
            (str(exp_date), category, description, amount))
        conn.commit()
        st.session_state.expense_df = pd.read_sql("SELECT * FROM daily_expenses", conn)
        conn.close()
        st.session_state.expense_desc_manual_input = ""
        st.session_state.expense_amount_input = 0.0
        st.session_state.expense_add_warning = False

    def _save_expense_edits(edited):
        conn = sqlite3.connect('enterprise.db')
        conn.execute("DELETE FROM daily_expenses")
        for row in edited.to_dict("records"):
            desc = row.get('description', '')
            if str(desc).strip():
                conn.execute(
                    "INSERT INTO daily_expenses (date, category, description, amount) VALUES (?,?,?,?)",
                    (row.get('date'), row.get('category'), desc, row.get('amount', 0) or 0))
        conn.commit()
        st.session_state.expense_df = pd.read_sql("SELECT * FROM daily_expenses", conn)
        conn.close()

    deals = st.session_state.business_df
    credit_tab, debit_tab, expense_tab = st.tabs([
        "💰 Credit Sheet (Client hume dega)",
        "💸 Debit Sheet (Hum client ko dengay)",
        "🧾 Daily Expense Sheet"
    ])

    # ---------------- CREDIT SHEET ----------------
    with credit_tab:
        # ---- Date filter for Credit Sheet (point 3) — applies to the deal-derived
        # rows only, since manual entries don't carry a date field ----
        _credit_dates = pd.to_datetime(deals['date'], errors='coerce') if not deals.empty else pd.Series([], dtype='datetime64[ns]')
        _credit_default_from = _credit_dates.min().date() if not _credit_dates.empty and _credit_dates.notna().any() else date.today()
        _credit_default_to = _credit_dates.max().date() if not _credit_dates.empty and _credit_dates.notna().any() else date.today()
        cf1, cf2 = st.columns(2)
        credit_from = cf1.date_input("From", value=_credit_default_from, key="credit_filter_from")
        credit_to = cf2.date_input("To", value=_credit_default_to, key="credit_filter_to")
        st.caption("Filter sirf deals wali entries par lagta hai — manual entries mein date nahi hoti, woh hamesha nazar aayengi.")

        auto_credit = deals[deals['remaining'] >= 0].copy() if not deals.empty else deals
        auto_credit = _apply_date_filter(auto_credit, 'date', credit_from, credit_to)
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

        full_credit_view = pd.concat([auto_credit_view, manual_c_view], ignore_index=True)

        st.subheader("📋 Full Credit Sheet")
        st.dataframe(full_credit_view, use_container_width=True, hide_index=True)

        # ---- Credit Sheet CSV / PDF export (landscape, "Credit Sheet" heading, no stamp/account) ----
        cec1, cec2 = st.columns(2)
        cec1.download_button("⬇️ Credit Sheet CSV", data=_df_to_csv_bytes(full_credit_view),
                              file_name="credit_sheet.csv", mime="text/csv", key="credit_csv_btn")
        credit_pdf_path = generate_sheet_pdf(full_credit_view, CREDIT_HEADERS, CREDIT_COL_WIDTHS,
                                              "Credit Sheet", "credit_sheet", orientation="L")
        with open(credit_pdf_path, "rb") as f:
            cec2.download_button("⬇️ Credit Sheet PDF", data=f, file_name="credit_sheet.pdf",
                                  mime="application/pdf", key="credit_pdf_btn")

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
            if st.button("💾 Save Credit Changes", key="save_credit_btn"):
                _save_credit_edits(edited_credit)
                st.success("Credit Sheet update ho gayi!")

    # ---------------- DEBIT SHEET ----------------
    with debit_tab:
        # ---- Date filter for Debit Sheet (point 3) — applies to the deal-derived
        # rows only, since manual entries don't carry a date field ----
        _debit_dates = pd.to_datetime(deals['date'], errors='coerce') if not deals.empty else pd.Series([], dtype='datetime64[ns]')
        _debit_default_from = _debit_dates.min().date() if not _debit_dates.empty and _debit_dates.notna().any() else date.today()
        _debit_default_to = _debit_dates.max().date() if not _debit_dates.empty and _debit_dates.notna().any() else date.today()
        df1, df2 = st.columns(2)
        debit_from = df1.date_input("From", value=_debit_default_from, key="debit_filter_from")
        debit_to = df2.date_input("To", value=_debit_default_to, key="debit_filter_to")
        st.caption("Filter sirf deals wali entries par lagta hai — manual entries mein date nahi hoti, woh hamesha nazar aayengi.")

        auto_debit = deals[deals['remaining'] < 0].copy() if not deals.empty else deals
        auto_debit = _apply_date_filter(auto_debit, 'date', debit_from, debit_to)
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

        full_debit_view = pd.concat([auto_debit_view, manual_d_view], ignore_index=True)

        st.subheader("📋 Full Debit Sheet")
        st.dataframe(full_debit_view, use_container_width=True, hide_index=True)

        # ---- Debit Sheet CSV / PDF export (landscape, "Debit Sheet" heading, no stamp/account) ----
        dec1, dec2 = st.columns(2)
        dec1.download_button("⬇️ Debit Sheet CSV", data=_df_to_csv_bytes(full_debit_view),
                              file_name="debit_sheet.csv", mime="text/csv", key="debit_csv_btn")
        debit_pdf_path = generate_sheet_pdf(full_debit_view, DEBIT_HEADERS, DEBIT_COL_WIDTHS,
                                             "Debit Sheet", "debit_sheet", orientation="L")
        with open(debit_pdf_path, "rb") as f:
            dec2.download_button("⬇️ Debit Sheet PDF", data=f, file_name="debit_sheet.pdf",
                                  mime="application/pdf", key="debit_pdf_btn")

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
            if st.button("💾 Save Debit Changes", key="save_debit_btn"):
                _save_debit_edits(edited_debit)
                st.success("Debit Sheet update ho gayi!")

    # ---------------- DAILY EXPENSE SHEET ----------------
    with expense_tab:
        st.subheader("🧾 Daily Expense Sheet")
        st.caption("Eating / Fuel select karne par description khud-ba-khud bhar jaati hai. "
                    "Others select karne par description khud likhni hogi.")

        ec1, ec2, ec3, ec4 = st.columns([1.2, 1.6, 1, 1])
        category = ec1.selectbox("Category", ["Eating", "Fuel", "Others"], key="expense_category_input")
        if category == "Others":
            ec2.text_input("Description", key="expense_desc_manual_input")
        else:
            ec2.text_input("Description", value=category, disabled=True)
        ec3.number_input("Amount", min_value=0.0, format="%g", key="expense_amount_input")
        ec4.date_input("Date", value=date.today(), key="expense_date_input")

        st.button("➕ Add Expense", on_click=_add_expense_cb, key="add_expense_btn")
        if st.session_state.get("expense_add_warning"):
            st.warning("Description likhna zaroori hai.")

        st.divider()
        st.subheader("📋 Full Expense Sheet")

        # ---- Date filter for Expense Sheet (point 3) ----
        _exp_dates = pd.to_datetime(st.session_state.expense_df['date'], errors='coerce') \
            if not st.session_state.expense_df.empty else pd.Series([], dtype='datetime64[ns]')
        _exp_default_from = _exp_dates.min().date() if not _exp_dates.empty and _exp_dates.notna().any() else date.today()
        _exp_default_to = _exp_dates.max().date() if not _exp_dates.empty and _exp_dates.notna().any() else date.today()
        ef1, ef2 = st.columns(2)
        expense_from = ef1.date_input("From", value=_exp_default_from, key="expense_filter_from")
        expense_to = ef2.date_input("To", value=_exp_default_to, key="expense_filter_to")

        filtered_expense_df = _apply_date_filter(
            st.session_state.expense_df.drop(columns=['id'], errors='ignore'), 'date', expense_from, expense_to)

        st.dataframe(filtered_expense_df, use_container_width=True, hide_index=True)

        # ---- Total of the entries currently shown (point 4) ----
        _expense_total = filtered_expense_df['amount'].sum() if not filtered_expense_df.empty else 0
        st.metric("💵 Total Expense (selected range)", f"Rs {_expense_total:,.0f}")

        # ---- Expense Sheet CSV / PDF export (point 4: portrait, only 2 columns, "Expense Sheet" heading) ----
        if not filtered_expense_df.empty:
            eec1, eec2 = st.columns(2)
            eec1.download_button("⬇️ Expense Sheet CSV",
                                  data=_df_to_csv_bytes(filtered_expense_df),
                                  file_name="expense_sheet.csv", mime="text/csv", key="expense_csv_btn")
            expense_pdf_df = filtered_expense_df[['description', 'amount']].rename(
                columns={'description': 'Description', 'amount': 'Amount'})
            expense_pdf_path = generate_sheet_pdf(expense_pdf_df, EXPENSE_HEADERS, EXPENSE_COL_WIDTHS,
                                                   "Expense Sheet", "expense_sheet", orientation="P")
            with open(expense_pdf_path, "rb") as f:
                eec2.download_button("⬇️ Expense Sheet PDF", data=f, file_name="expense_sheet.pdf",
                                      mime="application/pdf", key="expense_pdf_btn")

        if not st.session_state.expense_df.empty:
            st.write("**Manual Entries (editable)**")
            edited_expense = st.data_editor(
                st.session_state.expense_df.drop(columns=['id']),
                use_container_width=True, hide_index=True, num_rows="dynamic", key="expense_editor_data",
                column_config={
                    "category": st.column_config.SelectboxColumn("category", options=["Eating", "Fuel", "Others"])
                })
            if st.button("💾 Save Expense Changes", key="save_expense_btn"):
                _save_expense_edits(edited_expense)
                st.success("Expense Sheet update ho gayi!")

# ---------------- TAB 4: PERFORMANCE INSIGHTS ----------------
with tab4:
    st.title("📊 Performance Insights")

    # ---- Summary cards: monthly payments received, pending payments, profit, expense ----
    this_month = datetime.now().strftime("%Y-%m")
    biz = st.session_state.business_df.copy()
    if not biz.empty:
        biz_dates = pd.to_datetime(biz['date'], errors='coerce')
        monthly_paid = biz.loc[biz_dates.dt.strftime("%Y-%m") == this_month, 'paid'].sum()
        pending_total = biz.loc[biz['remaining'] > 0, 'remaining'].sum()
        total_profit = biz['profit'].sum()
    else:
        monthly_paid = pending_total = total_profit = 0

    exp = st.session_state.expense_df.copy()
    if not exp.empty:
        exp_dates = pd.to_datetime(exp['date'], errors='coerce')
        monthly_expense = exp.loc[exp_dates.dt.strftime("%Y-%m") == this_month, 'amount'].sum()
    else:
        monthly_expense = 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💰 Payments Received (This Month)", f"Rs {int(monthly_paid):,}")
    m2.metric("⏳ Pending Payments", f"Rs {int(pending_total):,}")
    m3.metric("📈 Total Profit", f"Rs {int(total_profit):,}")
    m4.metric("💸 Expenses (This Month)", f"Rs {int(monthly_expense):,}")

    st.divider()

    if not st.session_state.business_df.empty:
        st.metric("Total Revenue", f"Rs {int(st.session_state.business_df['close_deal'].sum()):,}")
        fig = px.bar(st.session_state.business_df, x='id', y='close_deal', template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
