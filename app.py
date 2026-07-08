import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('enterprise.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS home_finance (id INTEGER PRIMARY KEY, recipient TEXT, amount REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS business_deals 
                 (id INTEGER PRIMARY KEY, date TEXT, client TEXT, invoice_no TEXT, 
                  specs TEXT, equipment TEXT, quantity REAL, unit_price REAL, total REAL, 
                  cost REAL, paid REAL, remaining REAL, type TEXT, status TEXT, team_member TEXT)''')
    conn.commit()
    conn.close()

init_db()

st.set_page_config(page_title="Hameez Enterprise Hub", layout="wide")

# --- INITIALIZE SESSION STATE ---
if 'business_df' not in st.session_state:
    conn = sqlite3.connect('enterprise.db')
    st.session_state.business_df = pd.read_sql("SELECT * FROM business_deals", conn)
    conn.close()

tab1, tab2, tab3, tab4 = st.tabs(["🏠 Home Finance", "💼 Business Deals", "💳 Credit/Debit Sheets", "📊 Analytics"])

# --- TAB 1 ---
with tab1:
    st.title("🏡 Home Finance Tracker")
    conn = sqlite3.connect('enterprise.db')
    if st.button("Add General Entry"):
        conn.execute("INSERT INTO home_finance (recipient, amount) VALUES ('General', 0)")
        conn.commit()
        st.rerun()
    st.dataframe(pd.read_sql("SELECT * FROM home_finance", conn), use_container_width=True)
    conn.close()

# --- TAB 2: Business Deals ---
with tab2:
    st.title("➕ Register & Manage Medical Deal")
    
    with st.form("biz_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        client = c1.text_input("Client Name/Hospital")
        team_member = c2.text_input("Team Member (Optional)")
        
        c3, c4, c5, c6 = st.columns(4)
        specs = c3.text_input("SPECS")
        equipment = c4.text_input("Equipment")
        qty = c5.number_input("QUANTITY", min_value=0.0, format="%g")
        u_price = c6.number_input("Unit Price", min_value=0.0, format="%g")
        
        c7, c8 = st.columns(2)
        unit_actual_cost = c7.number_input("Per Unit Actual Cost", min_value=0.0, format="%g")
        paid = c8.number_input("Payment sent by Client", min_value=0.0, format="%g")
        
        if st.form_submit_button("Log Deal"):
            inv_no = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            total = qty * u_price
            actual_cost = qty * unit_actual_cost
            remaining = actual_cost - paid
            status = "Paid" if remaining <= 0 else "Pending"
            
            conn = sqlite3.connect('enterprise.db')
            # Table structure ke mutabiq columns ka order set kiya hai
            conn.execute("""INSERT INTO business_deals 
                          (date, client, invoice_no, specs, equipment, quantity, unit_price,Per Unit Actual Cost, total,actual_cost, cost, paid, remaining, type, status, team_member) 
                          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                         (datetime.now().strftime("%Y-%m-%d"), client, inv_no, specs, equipment, qty, u_price, total, actual_cost, paid, remaining, "Invoice", status, team_member))
            conn.commit()
            st.session_state.business_df = pd.read_sql("SELECT * FROM business_deals", conn)
            conn.close()
            st.rerun()
    st.subheader("📋 Recent Deals (Edit Remaining to 0 to Pay)")

    # Columns display order
    cols_order = ['date', 'invoice_no', 'client', 'equipment', 'specs', 'unit_price', 'total', 'cost', 'paid', 'remaining', 'team_member', 'status']
    
    # Data Editor
    edited_df = st.data_editor(
        st.session_state.business_df[cols_order], 
        use_container_width=True, 
        hide_index=True,
        key="data_editor_main"
    )

    if not edited_df.equals(st.session_state.business_df[cols_order]):
        # Recalculate logic for whole numbers
        edited_df["remaining"] = edited_df["total"] - edited_df["paid"]
        edited_df["status"] = edited_df["remaining"].apply(lambda x: "Paid" if x <= 0 else "Pending")
        
        # Save updated dataframe
        st.session_state.business_df.update(edited_df)
        
        conn = sqlite3.connect('enterprise.db')
        st.session_state.business_df.to_sql('business_deals', conn, if_exists='replace', index=False)
        conn.close()
        st.rerun()

    def highlight_remaining(val):
        color = '#ff4b4b' if isinstance(val, (int, float)) and val > 0 else ''
        return f'background-color: {color}'

    # Final Display with formatting
    st.dataframe(
        st.session_state.business_df[cols_order].style.format({
            "total": "{:.0f}", "paid": "{:.0f}", "remaining": "{:.0f}", "cost": "{:.0f}", "unit_price": "{:.0f}"
        }).map(highlight_remaining, subset=['remaining']),
        use_container_width=True
    )# --- TAB 3 & 4 remain functional ---
with tab3:
    st.title("💳 Financial Sheets")
    df = st.session_state.business_df
    if not df.empty:
        st.subheader("Credit Sheet (Receivables)")
        st.dataframe(df[['client', 'invoice_no', 'equipment', 'total', 'paid', 'remaining', 'status']], use_container_width=True)
        st.subheader("Debit Sheet (Liabilities)")
        st.dataframe(df[['client', 'invoice_no', 'equipment', 'cost', 'paid']], use_container_width=True)

with tab4:
    st.title("📊 Performance Insights")
    df_biz = st.session_state.business_df
    if not df_biz.empty:
        st.metric("Total Revenue", f"Rs {int(df_biz['total'].sum()):,}")
        fig = px.bar(df_biz, x='invoice_no', y='total', template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
