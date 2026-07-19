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

RECORD_DISPLAY_COLUMNS = ['id', 'date', 'client', 'equipment', 'specs', 'qty_per_item',
                          'close_deal', 'actual_cost', 'actual_price_per_item',
                          'other_expenses_per_item', 'paid', 'remaining', 'profit',
                          'team_member', 'status']
RECORD_DISPLAY_HEADERS = ['No.', 'Date', 'Client', 'Equipment', 'Specs', 'Qty',
                           'Close Deal', 'Actual Cost', 'Actual Price/Item',
                           'Other Expenses', 'Paid', 'Remaining', 'Profit',
                           'Team Member', 'Status']
RECORD_COL_WIDTHS = [10, 18, 26, 26, 22, 16, 18, 18, 20, 20, 16, 18, 16, 20, 13]  # sums to 277mm

CREDIT_HEADERS = ["Client Name", "Id No", "Total Payment", "Paid by Client", "Remaining from Client"]
CREDIT_COL_WIDTHS = [60, 35, 60, 60, 62]  # sums to 277mm

DEBIT_HEADERS = ["Client Name", "Id No", "Total Payment", "Paid to Client", "Remaining to be paid"]
DEBIT_COL_WIDTHS = [60, 35, 60, 60, 62]  # sums to 277mm

EXPENSE_HEADERS = ["Description", "Amount"]
EXPENSE_COL_WIDTHS = [130, 60]  # sums to 190mm (A4 portrait usable width)


# =========================================================================
# FORMATTING HELPERS
# =========================================================================

def _format_date_ddmmyyyy(value):
    try:
        return pd.to_datetime(value).strftime("%d-%m-%Y")
    except Exception:
        return value


def _fmt_money(value):
    try:
        return f"{float(value):,.0f}"
    except (TypeError, ValueError):
        return value


def _prepare_export_df(df, date_cols=(), money_cols=()):
    out = df.copy()
    for col in date_cols:
        if col in out.columns:
            out[col] = out[col].apply(_format_date_ddmmyyyy)
    for col in money_cols:
        if col in out.columns:
            out[col] = out[col].apply(_fmt_money)
    return out


def _parse_csv_floats(s):
    if s is None:
        return []
    out = []
    for p in str(s).split(','):
        p = p.strip()
        if not p or p.lower() in ('none', 'nan'):
            continue
        try:
            out.append(float(p))
        except ValueError:
            continue
    return out


_ONES = ["", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE",
         "TEN", "ELEVEN", "TWELVE", "THIRTEEN", "FOURTEEN", "FIFTEEN", "SIXTEEN",
         "SEVENTEEN", "EIGHTEEN", "NINETEEN"]
_TENS = ["", "", "TWENTY", "THIRTY", "FORTY", "FIFTY", "SIXTY", "SEVENTY", "EIGHTY", "NINETY"]


def _three_digit_words(n):
    words = ""
    if n >= 100:
        words += _ONES[n // 100] + " HUNDRED "
        n %= 100
    if n >= 20:
        words += _TENS[n // 10] + " "
        n %= 10
        if n:
            words += _ONES[n] + " "
    elif n > 0:
        words += _ONES[n] + " "
    return words.strip()


def _number_to_words(n):
    n = int(round(n))
    if n == 0:
        return "ZERO"
    negative = n < 0
    n = abs(n)
    parts = []
    for divisor, name in [(1_000_000_000, "BILLION"), (1_000_000, "MILLION"), (1_000, "THOUSAND")]:
        if n >= divisor:
            parts.append(f"{_three_digit_words(n // divisor)} {name}")
            n %= divisor
    if n > 0:
        parts.append(_three_digit_words(n))
    result = " ".join(parts).strip()
    return ("MINUS " + result) if negative else result


# --- PDF GENERATOR CLASS ---
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
    pdf.set_draw_color(0, 153, 224)
    pdf.set_font("Arial", "B", 7); pdf.set_fill_color(240, 240, 240)
    pdf.cell(15, 8, "SR #", 1, 0, "C", True); pdf.cell(45, 8, "PRODUCT", 1, 0, "C", True)
    pdf.cell(40, 8, "SPECS", 1, 0, "C", True); pdf.cell(15, 8, "QTY", 1, 0, "C", True)
    pdf.cell(25, 8, "PRICE PER UNIT IN PKR", 1, 0, "C", True); pdf.cell(25, 8, "TOTAL PRICE IN PKR", 1, 1, "C", True)


def _wrapped_line_count(pdf, text, width):
    """Estimates how many lines a multi_cell(width, ...) call will take for the
    given text -- used both for sizing the Terms & Conditions block AND (now)
    for auto-growing table rows so long names/specs never get cut off, they
    just wrap onto extra lines and the row grows taller automatically."""
    total_lines = 0
    for paragraph in str(text).split("\n"):
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


def _draw_wrapped_row(pdf, values, widths, line_h, start_x, align="C"):
    """Draws one table row where every cell auto-wraps long text onto multiple
    lines instead of cutting it off. The border for EVERY cell in the row is
    drawn at the same full row height (the tallest cell's height) first, then
    the (possibly multi-line) text is written on top without its own border --
    this keeps the whole row's grid lines aligned instead of only the
    long-text column's box stretching while the rest stay short."""
    n_lines = [_wrapped_line_count(pdf, v, w) for v, w in zip(values, widths)]
    row_h = max(n_lines) * line_h
    y0 = pdf.get_y()
    x = start_x
    for v, w in zip(values, widths):
        pdf.rect(x, y0, w, row_h)
        pdf.set_xy(x, y0)
        pdf.multi_cell(w, line_h, v, border=0, align=align)
        x += w
    pdf.set_xy(start_x, y0 + row_h)
    return row_h


def generate_pdf(deal, items_df, doc_type="Invoice", terms_text=None):
    pdf = InvoicePDF()
    pdf.add_page()
    blue_color = (0, 153, 224)
    pdf.set_draw_color(*blue_color)

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
    date_val = _format_date_ddmmyyyy(deal['date'])
    pdf.set_xy(155, 45); pdf.cell(pdf.get_string_width(date_val), 5, date_val)
    pdf.line(155, 50, 155 + pdf.get_string_width(date_val), 50)

    # 2. Client Name
    pdf.set_text_color(0, 0, 0); pdf.set_xy(15, 58); pdf.set_font("Arial", "B", 12)
    pdf.cell(10, 6, "To: ")
    name_x = pdf.get_x()
    client_name = f"{deal['client']}"
    pdf.set_font("Arial", "B", 12)
    pdf.cell(pdf.get_string_width(client_name), 6, client_name)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(name_x, 64, name_x + pdf.get_string_width(client_name), 64)

    # 3. Table
    pdf.set_xy(0, 70); pdf.set_font("Arial", "B", 16); pdf.cell(210, 8, doc_type.upper(), align="C")

    _draw_item_table_header(pdf, 85)
    pdf.set_font("Arial", "", 9)
    pdf.set_draw_color(0, 153, 224)

    item_widths = [15, 45, 40, 15, 25, 25]
    line_h = 5

    for i, item in enumerate(items_df.itertuples(), start=1):
        price_txt = "" if is_challan else f"{item.unit_price:,.0f}"
        total_txt = "" if is_challan else f"{item.line_total:,.0f}"
        values = [str(i), str(item.equipment), str(item.specs), f"{item.quantity:g}", price_txt, total_txt]

        n_lines = [_wrapped_line_count(pdf, v, w) for v, w in zip(values, item_widths)]
        row_h = max(n_lines) * line_h

        if pdf.get_y() + row_h > 250:
            pdf.add_page(); _draw_item_table_header(pdf, 45)
            pdf.set_font("Arial", "", 9); pdf.set_draw_color(0, 153, 224)

        _draw_wrapped_row(pdf, values, item_widths, line_h, start_x=25)

    if pdf.get_y() + 20 > 250:
        pdf.add_page()

    if not is_challan:
        pdf.set_x(125); pdf.set_font("Arial", "B", 10)
        pdf.cell(40, 8, "Grand Total", 1, 0, "C", True)
        pdf.cell(25, 8, f"{deal['close_deal']:,.0f}", 1, 1, "C", True)

        pdf.set_x(15)
        pdf.set_font("Arial", "B", 8)
        pdf.cell(175, 5, f"{_number_to_words(deal['close_deal'])} RUPEES ONLY", align="R")
        pdf.ln(6)

    show_terms = doc_type == "Quotation" and terms_text and terms_text.strip()
    divider_y = 222

    if show_terms:
        if pdf.get_y() + 10 > 195:
            pdf.add_page()
        terms_y = pdf.get_y() + 10
        pdf.set_xy(15, terms_y)
        pdf.set_font("Arial", "B", 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 6, "Terms & Conditions:", ln=1)
        pdf.set_x(15)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(90, 5, terms_text)

    if pdf.get_y() + 10 > divider_y:
        pdf.add_page()

    content_y = divider_y + 3

    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, divider_y, 200, divider_y)

    pdf.set_xy(15, content_y)
    pdf.set_font("Arial", "I", 9)
    pdf.cell(90, 5, "Regards,", ln=1)

    pdf.set_x(15)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(90, 5, "Badar Diagnostics & Medical Equipment, Lahore", ln=1)

    pdf.set_x(15)
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(90, 5, "Account Details:", ln=1)

    pdf.set_x(15)
    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(90, 4, "Badar Diagnostics & Medical Equipment\nFaysal Bank\n0155007000005585")

    if os.path.exists("stamp.jpg"):
        pdf.image("stamp.jpg", x=140, y=content_y, w=35)

    file_path = f"{doc_type.replace(' ', '_')}_{deal['invoice_no']}.pdf"
    pdf.output(file_path)
    return file_path


# =========================================================================
# GENERIC SHEET EXPORT (Records / Credit Sheet / Debit Sheet / Expense Sheet)
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

    line_h = 5
    y = table_y + 8
    bottom_limit = pdf.h - 45  # leave room for the letterhead footer band

    for _, row in df.iterrows():
        values = ["" if pd.isna(v) else str(v) for v in row.tolist()]
        n_lines = [_wrapped_line_count(pdf, v, w) for v, w in zip(values, col_widths)]
        row_h = max(n_lines) * line_h

        if y + row_h > bottom_limit:
            pdf.add_page()
            y = title_y
            _draw_sheet_table_header(pdf, headers, col_widths, y, start_x)
            pdf.set_font("Arial", "", 8); pdf.set_draw_color(0, 153, 224)
            y += 8

        pdf.set_xy(start_x, y)
        _draw_wrapped_row(pdf, values, col_widths, line_h, start_x)
        y += row_h

    path = f"{filename_prefix}.pdf"
    pdf.output(path)
    return path


def _df_to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8-sig")


def _apply_date_filter(df, date_col, start, end):
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
                  equipment TEXT, specs TEXT, qty_per_item TEXT, close_deal REAL, actual_cost REAL,
                  actual_price_per_item TEXT, other_expenses_per_item TEXT,
                  paid REAL, remaining REAL, profit REAL, team_member TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS deal_items
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, deal_id INTEGER, equipment TEXT, specs TEXT,
                  quantity REAL, unit_price REAL, unit_actual_cost REAL, other_expenses REAL,
                  line_total REAL, line_actual_cost REAL,
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

    existing_cols = [row[1] for row in c.execute("PRAGMA table_info(business_deals)").fetchall()]
    if 'equipment' not in existing_cols:
        c.execute("ALTER TABLE business_deals ADD COLUMN equipment TEXT")
    if 'specs' not in existing_cols:
        c.execute("ALTER TABLE business_deals ADD COLUMN specs TEXT")
    if 'actual_price_per_item' not in existing_cols:
        c.execute("ALTER TABLE business_deals ADD COLUMN actual_price_per_item TEXT")
    if 'qty_per_item' not in existing_cols:
        c.execute("ALTER TABLE business_deals ADD COLUMN qty_per_item TEXT")
    if 'other_expenses_per_item' not in existing_cols:
        c.execute("ALTER TABLE business_deals ADD COLUMN other_expenses_per_item TEXT")

    existing_item_cols = [row[1] for row in c.execute("PRAGMA table_info(deal_items)").fetchall()]
    if 'other_expenses' not in existing_item_cols:
        c.execute("ALTER TABLE deal_items ADD COLUMN other_expenses REAL DEFAULT 0")

    conn.commit(); conn.close()


init_db()
st.set_page_config(page_title="Hameez Enterprise Hub", layout="wide")

if 'business_df' not in st.session_state:
    conn = sqlite3.connect('enterprise.db')
    st.session_state.business_df = pd.read_sql("SELECT * FROM business_deals", conn); conn.close()

if 'temp_items' not in st.session_state:
    st.session_state.temp_items = []

if 'update_temp_items' not in st.session_state:
    st.session_state.update_temp_items = []

if 'editing_deal_id' not in st.session_state:
    st.session_state.editing_deal_id = None

if 'confirm_delete_deal_id' not in st.session_state:
    st.session_state.confirm_delete_deal_id = None

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

    def _add_item_cb():
        name = st.session_state.item_name_input
        if name and name.strip():
            qty = st.session_state.item_qty_input
            price = st.session_state.item_price_input
            cost = st.session_state.item_cost_input
            other = st.session_state.item_other_input
            st.session_state.temp_items.append({
                'equipment': name,
                'specs': st.session_state.item_specs_input,
                'quantity': qty,
                'unit_price': price,
                'unit_actual_cost': cost,
                'other_expenses': other,
                'line_total': qty * price,
                'line_actual_cost': qty * cost + other,
            })
            st.session_state.item_name_input = ""
            st.session_state.item_specs_input = ""
            st.session_state.item_qty_input = 1
            st.session_state.item_price_input = 0.0
            st.session_state.item_cost_input = 0.0
            st.session_state.item_other_input = 0.0
            st.session_state.add_item_warning = False
        else:
            st.session_state.add_item_warning = True

    def _remove_item_cb(idx):
        if 0 <= idx < len(st.session_state.temp_items):
            st.session_state.temp_items.pop(idx)

    def _log_deal_cb():
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

        if len(items) == 1:
            equipment_display = items[0]['equipment']
            specs_display = items[0]['specs']
        else:
            equipment_display = ", ".join(i['equipment'] for i in items)
            specs_display = "Multiple Items"

        qty_display = ", ".join(f"{i['quantity']:g}" for i in items)
        actual_price_display = ", ".join(f"{i['unit_actual_cost']:.0f}" for i in items)
        other_expenses_display = ", ".join(f"{i['other_expenses']:.0f}" for i in items)

        conn = sqlite3.connect('enterprise.db')
        cur = conn.cursor()
        cur.execute("""INSERT INTO business_deals
            (date, invoice_no, client, equipment, specs, qty_per_item, close_deal, actual_cost,
             actual_price_per_item, other_expenses_per_item, paid, remaining, profit, team_member, status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (datetime.now().strftime("%Y-%m-%d"), inv_no, st.session_state.deal_client, equipment_display,
             specs_display, qty_display, close_deal, actual_cost, actual_price_display, other_expenses_display,
             paid, remaining, profit, st.session_state.deal_team_member, status))
        deal_id = cur.lastrowid

        for item in items:
            cur.execute("""INSERT INTO deal_items
                (deal_id, equipment, specs, quantity, unit_price, unit_actual_cost, other_expenses, line_total, line_actual_cost)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (deal_id, item['equipment'], item['specs'], item['quantity'], item['unit_price'],
                 item['unit_actual_cost'], item['other_expenses'], item['line_total'], item['line_actual_cost']))

        conn.commit()
        st.session_state.business_df = pd.read_sql("SELECT * FROM business_deals", conn)
        conn.close()

        st.session_state.temp_items = []
        st.session_state.deal_client = ""
        st.session_state.deal_team_member = ""
        st.session_state.deal_paid = 0.0
        st.session_state.deal_message = ("success", f"Deal {inv_no} save ho gayi!")

    def _save_records_edits(edited):
        conn = sqlite3.connect('enterprise.db')
        cur = conn.cursor()
        for row in edited.to_dict("records"):
            deal_id = row.get('id')
            close_deal = row.get('close_deal', 0) or 0
            paid = row.get('paid', 0) or 0

            qty_list = _parse_csv_floats(row.get('qty_per_item'))
            price_list = _parse_csv_floats(row.get('actual_price_per_item'))
            other_list = _parse_csv_floats(row.get('other_expenses_per_item'))

            if qty_list and price_list and other_list and len(qty_list) == len(price_list) == len(other_list):
                line_costs = [q * p + o for q, p, o in zip(qty_list, price_list, other_list)]
                actual_cost = sum(line_costs)
                item_ids = [r[0] for r in cur.execute(
                    "SELECT id FROM deal_items WHERE deal_id=? ORDER BY id", (int(deal_id),)).fetchall()]
                if len(item_ids) == len(qty_list):
                    for item_id, q, p, o, lc in zip(item_ids, qty_list, price_list, other_list, line_costs):
                        cur.execute("UPDATE deal_items SET quantity=?, unit_actual_cost=?, other_expenses=?, "
                                    "line_actual_cost=? WHERE id=?", (q, p, o, lc, item_id))
            else:
                actual_cost = row.get('actual_cost', 0) or 0

            remaining_edited = row.get('remaining', None)
            if remaining_edited is not None and abs(remaining_edited - (close_deal - paid)) > 0.01:
                remaining = remaining_edited
                paid = close_deal - remaining
            else:
                remaining = close_deal - paid
            profit = close_deal - actual_cost
            status = "Paid" if remaining <= 0.01 else "Pending"
            cur.execute("""UPDATE business_deals SET date=?, client=?, equipment=?, specs=?, qty_per_item=?,
                           close_deal=?, actual_cost=?, actual_price_per_item=?, other_expenses_per_item=?,
                           paid=?, remaining=?, profit=?, team_member=?, status=? WHERE id=?""",
                        (row.get('date'), row.get('client'), row.get('equipment'), row.get('specs'),
                         row.get('qty_per_item'), close_deal, actual_cost, row.get('actual_price_per_item'),
                         row.get('other_expenses_per_item'), paid, remaining, profit, row.get('team_member'),
                         status, deal_id))
        conn.commit()
        st.session_state.business_df = pd.read_sql("SELECT * FROM business_deals", conn)
        conn.close()

    def _delete_deal_cb(deal_id):
        """Point 4: permanently deletes a whole deal (and its line items)."""
        deal_id = int(deal_id)
        conn = sqlite3.connect('enterprise.db')
        cur = conn.cursor()
        cur.execute("DELETE FROM deal_items WHERE deal_id=?", (deal_id,))
        cur.execute("DELETE FROM business_deals WHERE id=?", (deal_id,))
        conn.commit()
        st.session_state.business_df = pd.read_sql("SELECT * FROM business_deals", conn)
        conn.close()
        if st.session_state.get("editing_deal_id") == deal_id:
            st.session_state.editing_deal_id = None
            st.session_state.update_temp_items = []
        st.session_state.confirm_delete_deal_id = None
        st.session_state.deal_delete_message = ("success", f"Deal #{deal_id} permanently delete ho gayi.")

    def _request_delete_deal_cb(deal_id):
        st.session_state.confirm_delete_deal_id = int(deal_id)

    def _cancel_delete_deal_cb():
        st.session_state.confirm_delete_deal_id = None

    def _save_existing_items_cb(deal_id, edited_df):
        """Point 3: lets you correct a wrong equipment/specs/qty/price entry on an
        existing deal, and also delete individual line items (via the editor's
        built-in row-delete). Recomputes the parent deal's totals afterwards."""
        deal_id = int(deal_id)
        conn = sqlite3.connect('enterprise.db')
        cur = conn.cursor()
        kept_ids = []
        for row in edited_df.to_dict("records"):
            if not str(row.get('equipment', '')).strip():
                continue
            qty = row.get('quantity') or 0
            price = row.get('unit_price') or 0
            cost = row.get('unit_actual_cost') or 0
            other = row.get('other_expenses') or 0
            line_total = qty * price
            line_actual_cost = qty * cost + other
            raw_id = row.get('id')
            if raw_id is not None and not pd.isna(raw_id):
                item_id = int(raw_id)
                kept_ids.append(item_id)
                cur.execute("""UPDATE deal_items SET equipment=?, specs=?, quantity=?, unit_price=?,
                               unit_actual_cost=?, other_expenses=?, line_total=?, line_actual_cost=?
                               WHERE id=?""",
                            (row.get('equipment'), row.get('specs'), qty, price, cost, other,
                             line_total, line_actual_cost, item_id))
            else:
                cur.execute("""INSERT INTO deal_items
                    (deal_id, equipment, specs, quantity, unit_price, unit_actual_cost, other_expenses, line_total, line_actual_cost)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (deal_id, row.get('equipment'), row.get('specs'), qty, price, cost, other,
                     line_total, line_actual_cost))

        all_existing_ids = [r[0] for r in cur.execute(
            "SELECT id FROM deal_items WHERE deal_id=?", (deal_id,)).fetchall()]
        for item_id in all_existing_ids:
            if item_id not in kept_ids:
                cur.execute("DELETE FROM deal_items WHERE id=?", (item_id,))
        conn.commit()

        all_items_df = pd.read_sql("SELECT * FROM deal_items WHERE deal_id=?", conn, params=(deal_id,))
        if all_items_df.empty:
            close_deal = 0.0; actual_cost = 0.0
            equipment_display = ""; specs_display = ""
            qty_display = ""; actual_price_display = ""; other_expenses_display = ""
        else:
            close_deal = all_items_df['line_total'].sum()
            actual_cost = all_items_df['line_actual_cost'].sum()
            if len(all_items_df) == 1:
                equipment_display = all_items_df.iloc[0]['equipment']
                specs_display = all_items_df.iloc[0]['specs']
            else:
                equipment_display = ", ".join(all_items_df['equipment'].tolist())
                specs_display = "Multiple Items"
            qty_display = ", ".join(f"{v:g}" for v in all_items_df['quantity'].tolist())
            actual_price_display = ", ".join(f"{v:.0f}" for v in all_items_df['unit_actual_cost'].tolist())
            other_expenses_display = ", ".join(f"{v:.0f}" for v in all_items_df['other_expenses'].tolist())

        old_row = st.session_state.business_df[st.session_state.business_df['id'] == deal_id].iloc[0]
        paid = old_row['paid']
        remaining = close_deal - paid
        profit = close_deal - actual_cost
        status = "Paid" if remaining <= 0.01 else "Pending"

        cur.execute("""UPDATE business_deals SET equipment=?, specs=?, qty_per_item=?, close_deal=?,
                       actual_cost=?, actual_price_per_item=?, other_expenses_per_item=?,
                       remaining=?, profit=?, status=? WHERE id=?""",
                    (equipment_display, specs_display, qty_display, close_deal, actual_cost,
                     actual_price_display, other_expenses_display, remaining, profit, status, deal_id))
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

        c5, c6, c7, c8 = st.columns(4)
        item_qty = c5.number_input("Qty", min_value=1, format="%g", key="item_qty_input")
        item_price = c6.number_input("Unit Price", min_value=0.0, format="%g", key="item_price_input")
        item_cost = c7.number_input("Actual Cost per Unit", min_value=0.0, format="%g", key="item_cost_input")
        item_other = c8.number_input("Other Expenses", min_value=0.0, format="%g", key="item_other_input")

        paid = st.number_input("Payment sent by Client", min_value=0.0, format="%g", key="deal_paid")

        st.button("➕ Add to List", use_container_width=True, on_click=_add_item_cb)
        if st.session_state.get("add_item_warning"):
            st.warning("Equipment Name likhna zaroori hai.")

        if st.session_state.temp_items:
            st.write("**Added Items:**")
            for idx, item in enumerate(st.session_state.temp_items):
                ic1, ic2, ic3, ic4, ic5, ic6, ic7 = st.columns([2, 2, 1, 1, 1, 1, 0.6])
                ic1.write(item['equipment']); ic2.write(item['specs'])
                ic3.write(f"{item['quantity']:g}"); ic4.write(f"{item['unit_price']:.0f}")
                ic5.write(f"{item['other_expenses']:.0f}")
                ic6.write(f"{item['line_total']:.0f}")
                ic7.button("🗑️", key=f"del_item_{idx}", on_click=_remove_item_cb, args=(idx,))
            st.caption(f"Running Total: Rs {sum(i['line_total'] for i in st.session_state.temp_items):,.0f}")

    with st.form("deal_form", clear_on_submit=True):
        st.form_submit_button("✅ Log Deal", use_container_width=True, on_click=_log_deal_cb)

    if st.session_state.get("deal_message"):
        level, text = st.session_state.deal_message
        getattr(st, level)(text)
        st.session_state.deal_message = None

    st.divider()
    st.subheader("📋 Records")

    _all_dates = pd.to_datetime(st.session_state.business_df['date'], errors='coerce') \
        if not st.session_state.business_df.empty else pd.Series([], dtype='datetime64[ns]')
    _default_from = _all_dates.min().date() if not _all_dates.empty and _all_dates.notna().any() else date.today()
    _default_to = _all_dates.max().date() if not _all_dates.empty and _all_dates.notna().any() else date.today()
    rf1, rf2 = st.columns(2)
    records_from = rf1.date_input("From", value=_default_from, key="records_filter_from")
    records_to = rf2.date_input("To", value=_default_to, key="records_filter_to")

    display_df = st.session_state.business_df.copy()
    for col in RECORD_DISPLAY_COLUMNS:
        if col not in display_df.columns:
            display_df[col] = None
    display_df = display_df[RECORD_DISPLAY_COLUMNS]
    display_df = _apply_date_filter(display_df, 'date', records_from, records_to)

    edited_records = st.data_editor(
        display_df, use_container_width=True, hide_index=True, num_rows="fixed",
        disabled=["id"], key="records_editor_data"
    )
    if st.button("💾 Save Records Changes", key="save_records_btn"):
        _save_records_edits(edited_records)
        st.success("Records update ho gaye!")

    if not display_df.empty:
        export_df = display_df.sort_values('id', ascending=False)
        export_df = _prepare_export_df(
            export_df, date_cols=['date'],
            money_cols=['close_deal', 'actual_cost', 'paid', 'remaining', 'profit'])
        export_df_named = export_df.rename(columns=dict(zip(RECORD_DISPLAY_COLUMNS, RECORD_DISPLAY_HEADERS)))
        rc1, rc2 = st.columns(2)
        rc1.download_button("⬇️ Records CSV", data=_df_to_csv_bytes(export_df_named),
                             file_name="records.csv", mime="text/csv", key="records_csv_btn")
        records_pdf_path = generate_sheet_pdf(export_df, RECORD_DISPLAY_HEADERS, RECORD_COL_WIDTHS,
                                               "Records", "records_sheet", orientation="L")
        with open(records_pdf_path, "rb") as f:
            rc2.download_button("⬇️ Records PDF", data=f, file_name="records.pdf",
                                 mime="application/pdf", key="records_pdf_btn")

    # =====================================================================
    # Manage Deals — Edit / Correct / Add Items / Delete Whole Deal
    # =====================================================================
    st.divider()
    st.subheader("🔧 Deals Manage Karein (Items Add/Edit/Delete)")
    st.caption("➕ Items = naye items add karein. ✏️ Correct = ghalat equipment/specs/qty/price theek karein "
               "ya koi item delete karein. 🗑️ Delete = puri deal hamesha ke liye delete karein.")

    if st.session_state.get("deal_delete_message"):
        level, text = st.session_state.deal_delete_message
        getattr(st, level)(text)
        st.session_state.deal_delete_message = None

    if not st.session_state.business_df.empty:

        def _select_deal_to_edit_cb(deal_id):
            st.session_state.editing_deal_id = deal_id
            st.session_state.update_temp_items = []

        header_c1, header_c2, header_c3, header_c4, header_c5 = st.columns([1, 3, 2, 1, 1])
        header_c1.markdown("**No.**"); header_c2.markdown("**Client**")
        header_c3.markdown("**Close Deal**"); header_c4.markdown("**Manage**"); header_c5.markdown("**Delete**")

        for _, drow in st.session_state.business_df.sort_values('id', ascending=False).iterrows():
            d_id = int(drow['id'])
            rcol1, rcol2, rcol3, rcol4, rcol5 = st.columns([1, 3, 2, 1, 1])
            rcol1.write(f"#{d_id}")
            rcol2.write(drow['client'])
            rcol3.write(f"Rs {drow['close_deal']:,.0f}")
            rcol4.button("✏️ Manage", key=f"edit_deal_btn_{d_id}",
                        on_click=_select_deal_to_edit_cb, args=(d_id,))

            if st.session_state.get("confirm_delete_deal_id") == d_id:
                dcol_a, dcol_b = rcol5.columns(2)
                dcol_a.button("✅", key=f"confirm_del_{d_id}", on_click=_delete_deal_cb, args=(d_id,),
                              type="primary", help="Confirm delete")
                dcol_b.button("✖️", key=f"cancel_del_{d_id}", on_click=_cancel_delete_deal_cb,
                              help="Cancel")
            else:
                rcol5.button("🗑️", key=f"del_deal_btn_{d_id}", on_click=_request_delete_deal_cb, args=(d_id,))

        if st.session_state.get("editing_deal_id") is not None:
            edit_deal_id = st.session_state.editing_deal_id

            with st.container(border=True):
                st.markdown(f"**Deal #{edit_deal_id} manage kar rahe hain:**")

                conn = sqlite3.connect('enterprise.db')
                existing_items_df = pd.read_sql(
                    "SELECT id, equipment, specs, quantity, unit_price, unit_actual_cost, other_expenses, line_total "
                    "FROM deal_items WHERE deal_id = ?", conn, params=(int(edit_deal_id),))
                conn.close()

                st.write("**✏️ Existing items (yahan se ghalti theek karein, ya row delete karein):**")
                edited_existing_items = st.data_editor(
                    existing_items_df, use_container_width=True, hide_index=True,
                    num_rows="dynamic", disabled=["id", "line_total"],
                    key=f"existing_items_editor_{edit_deal_id}"
                )
                if st.button("💾 Correction Save Karein", key=f"save_existing_items_btn_{edit_deal_id}"):
                    _save_existing_items_cb(edit_deal_id, edited_existing_items)
                    st.success(f"Deal #{edit_deal_id} ke items update ho gaye!")
                    st.rerun()

                st.divider()
                st.write("**➕ Deal mein bilkul naya item add karein:**")

                uc3, uc4 = st.columns(2)
                uc3.text_input("Equipment Name", key="update_item_name_input")
                uc4.text_input("Specs", key="update_item_specs_input")
                uc5, uc6, uc7, uc8 = st.columns(4)
                uc5.number_input("Qty", min_value=1, format="%g", key="update_item_qty_input")
                uc6.number_input("Unit Price", min_value=0.0, format="%g", key="update_item_price_input")
                uc7.number_input("Actual Cost per Unit", min_value=0.0, format="%g", key="update_item_cost_input")
                uc8.number_input("Other Expenses", min_value=0.0, format="%g", key="update_item_other_input")

                def _add_update_item_cb():
                    name = st.session_state.update_item_name_input
                    if name and name.strip():
                        qty = st.session_state.update_item_qty_input
                        price = st.session_state.update_item_price_input
                        cost = st.session_state.update_item_cost_input
                        other = st.session_state.update_item_other_input
                        st.session_state.update_temp_items.append({
                            'equipment': name,
                            'specs': st.session_state.update_item_specs_input,
                            'quantity': qty,
                            'unit_price': price,
                            'unit_actual_cost': cost,
                            'other_expenses': other,
                            'line_total': qty * price,
                            'line_actual_cost': qty * cost + other,
                        })
                        st.session_state.update_item_name_input = ""
                        st.session_state.update_item_specs_input = ""
                        st.session_state.update_item_qty_input = 1
                        st.session_state.update_item_price_input = 0.0
                        st.session_state.update_item_cost_input = 0.0
                        st.session_state.update_item_other_input = 0.0
                        st.session_state.update_add_item_warning = False
                    else:
                        st.session_state.update_add_item_warning = True

                st.button("➕ Add to List", key="update_add_item_btn", on_click=_add_update_item_cb)
                if st.session_state.get("update_add_item_warning"):
                    st.warning("Equipment Name likhna zaroori hai.")

                def _remove_update_item_cb(idx):
                    if 0 <= idx < len(st.session_state.update_temp_items):
                        st.session_state.update_temp_items.pop(idx)

                if st.session_state.update_temp_items:
                    st.write("**Naye Items (abhi save nahi huay):**")
                    for idx, item in enumerate(st.session_state.update_temp_items):
                        nic1, nic2, nic3, nic4, nic5, nic6, nic7 = st.columns([2, 2, 1, 1, 1, 1, 0.6])
                        nic1.write(item['equipment']); nic2.write(item['specs'])
                        nic3.write(f"{item['quantity']:g}"); nic4.write(f"{item['unit_price']:.0f}")
                        nic5.write(f"{item['other_expenses']:.0f}")
                        nic6.write(f"{item['line_total']:.0f}")
                        nic7.button("🗑️", key=f"del_update_item_{idx}",
                                    on_click=_remove_update_item_cb, args=(idx,))

                    def _update_deal_cb():
                        deal_id = int(edit_deal_id)
                        new_items = st.session_state.update_temp_items
                        if not new_items:
                            return
                        conn = sqlite3.connect('enterprise.db')
                        cur = conn.cursor()
                        for item in new_items:
                            cur.execute("""INSERT INTO deal_items
                                (deal_id, equipment, specs, quantity, unit_price, unit_actual_cost, other_expenses, line_total, line_actual_cost)
                                VALUES (?,?,?,?,?,?,?,?,?)""",
                                (deal_id, item['equipment'], item['specs'], item['quantity'], item['unit_price'],
                                 item['unit_actual_cost'], item['other_expenses'], item['line_total'], item['line_actual_cost']))
                        conn.commit()

                        all_items_df = pd.read_sql("SELECT * FROM deal_items WHERE deal_id=?", conn, params=(deal_id,))
                        close_deal = all_items_df['line_total'].sum()
                        actual_cost = all_items_df['line_actual_cost'].sum()
                        if len(all_items_df) == 1:
                            equipment_display = all_items_df.iloc[0]['equipment']
                            specs_display = all_items_df.iloc[0]['specs']
                        else:
                            equipment_display = ", ".join(all_items_df['equipment'].tolist())
                            specs_display = "Multiple Items"
                        qty_display = ", ".join(f"{v:g}" for v in all_items_df['quantity'].tolist())
                        actual_price_display = ", ".join(f"{v:.0f}" for v in all_items_df['unit_actual_cost'].tolist())
                        other_expenses_display = ", ".join(f"{v:.0f}" for v in all_items_df['other_expenses'].tolist())

                        old_row = st.session_state.business_df[st.session_state.business_df['id'] == deal_id].iloc[0]
                        paid = old_row['paid']
                        remaining = close_deal - paid
                        profit = close_deal - actual_cost
                        status = "Paid" if remaining <= 0.01 else "Pending"

                        cur.execute("""UPDATE business_deals SET equipment=?, specs=?, qty_per_item=?, close_deal=?,
                                       actual_cost=?, actual_price_per_item=?, other_expenses_per_item=?,
                                       remaining=?, profit=?, status=? WHERE id=?""",
                                    (equipment_display, specs_display, qty_display, close_deal, actual_cost,
                                     actual_price_display, other_expenses_display, remaining, profit, status, deal_id))
                        conn.commit()
                        st.session_state.business_df = pd.read_sql("SELECT * FROM business_deals", conn)
                        conn.close()

                        st.session_state.update_temp_items = []
                        st.session_state.editing_deal_id = None
                        st.session_state.update_deal_message = (
                            "success", f"Deal #{deal_id} update ho gayi — naye items add hogaye! "
                                       f"Ab is deal ki Invoice/Quotation/Challan updated items ke sath print hogi.")

                    st.button("💾 Deal Update Karein (Naye Items Save Karein)", key="update_deal_btn",
                             on_click=_update_deal_cb, type="primary")

                def _cancel_edit_deal_cb():
                    st.session_state.editing_deal_id = None
                    st.session_state.update_temp_items = []

                st.button("✖️ Band Karein", key="cancel_edit_deal_btn", on_click=_cancel_edit_deal_cb)

        if st.session_state.get("update_deal_message"):
            level, text = st.session_state.update_deal_message
            getattr(st, level)(text)
            st.session_state.update_deal_message = None

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

        if not full_credit_view.empty:
            full_credit_export = _prepare_export_df(
                full_credit_view,
                money_cols=["Total Payment", "Paid by Client", "Remaining from Client"])
            cec1, cec2 = st.columns(2)
            cec1.download_button("⬇️ Credit Sheet CSV", data=_df_to_csv_bytes(full_credit_export),
                                  file_name="credit_sheet.csv", mime="text/csv", key="credit_csv_btn")
            credit_pdf_path = generate_sheet_pdf(full_credit_export, CREDIT_HEADERS, CREDIT_COL_WIDTHS,
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

        if not full_debit_view.empty:
            full_debit_export = _prepare_export_df(
                full_debit_view,
                money_cols=["Total Payment", "Paid to Client", "Remaining to be paid"])
            dec1, dec2 = st.columns(2)
            dec1.download_button("⬇️ Debit Sheet CSV", data=_df_to_csv_bytes(full_debit_export),
                                  file_name="debit_sheet.csv", mime="text/csv", key="debit_csv_btn")
            debit_pdf_path = generate_sheet_pdf(full_debit_export, DEBIT_HEADERS, DEBIT_COL_WIDTHS,
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

        _expense_total = filtered_expense_df['amount'].sum() if not filtered_expense_df.empty else 0
        st.metric("💵 Total Expense (selected range)", f"Rs {_expense_total:,.0f}")

        if not filtered_expense_df.empty:
            expense_export = _prepare_export_df(filtered_expense_df, date_cols=['date'], money_cols=['amount'])
            eec1, eec2 = st.columns(2)
            eec1.download_button("⬇️ Expense Sheet CSV",
                                  data=_df_to_csv_bytes(expense_export),
                                  file_name="expense_sheet.csv", mime="text/csv", key="expense_csv_btn")
            expense_pdf_df = expense_export[['description', 'amount']].rename(
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
