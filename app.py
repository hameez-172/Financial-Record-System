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
    # Added team_member column
    c.execute('''CREATE TABLE IF NOT EXISTS business_deals 
                 (id INTEGER PRIMARY KEY, date TEXT, client TEXT, invoice_no TEXT, 
                  specs TEXT, quantity REAL, unit_price REAL, total REAL, 
                  cost REAL, paid REAL, remaining REAL, type TEXT, status TEXT, team_member TEXT)''')
    conn.commit()
    conn.close()

init_db()

st.set_page_config(page_title="Hameez Enterprise Hub", layout="wide")

tab1, tab2, tab3, tab4 = st.tabs(["🏠 Home Finance", "💼 Business Deals", "💳 Credit/Debit Sheets", "📊 Analytics"])

# --- TAB 1 ---
with tab1:
    st.title("🏡 Home Finance Tracker")
    conn = sqlite3.connect('enterprise.db')
    if st.button("Add General Entry"):
        conn.execute("INSERT INTO home_finance (recipient, amount) VALUES ('General', 0)")
        conn.commit()
    st.dataframe(pd.read_sql("SELECT * FROM home_finance", conn), use_container_width=True)
    conn.close()

# --- TAB 2: Business Deals ---
with tab2:
    st.title("➕ Register & Manage Medical Deal")
    
    with st.form("biz_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        client = c1.text_input("Client Name")
        team_member = c2.text_input("Team Member (Optional)")
        
        c3, c4, c5 = st.columns(3)
        specs = c3.text_input("SPECS")
        qty = c4.number_input("QUANTITY", min_value=0.0, format="%g")
        u_price = c5.number_input("PER UNIT PRICE", min_value=0.0, format="%g")
        
        if st.form_submit_button("Log Deal"):
            # Auto-generate unique invoice number
            inv_no = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            total = qty * u_price
            # Paid set to 0 initially, to be edited later
            paid = 0.0
            rem = total - paid
            status = "Pending"
            
            conn = sqlite3.connect('enterprise.db')
            conn.execute("INSERT INTO business_deals (date, client, invoice_no, specs, quantity, unit_price, total, cost, paid, remaining, type, status, team_member) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                         (datetime.now().strftime("%Y-%m-%d"), client, inv_no, specs, qty, u_price, total, 0, paid, rem, "Invoice", status, team_member))
            conn.commit()
            conn.close()
            st.rerun()

    conn = sqlite3.connect('enterprise.db')
    df_biz = pd.read_sql("SELECT * FROM business_deals", conn)
    
    st.subheader("📋 Edit Recent Deals")
    # Configuration to format numbers without decimals
    config = {
        "total": st.column_config.NumberColumn(format="%d"),
        "paid": st.column_config.NumberColumn(format="%d"),
        "remaining": st.column_config.NumberColumn(format="%d"),
        "quantity": st.column_config.NumberColumn(format="%g"),
        "unit_price": st.column_config.NumberColumn(format="%d")
    }
    
    edited_df = st.data_editor(df_biz, use_container_width=True, column_config=config)
    
    if st.button("Save Changes to Database"):
        edited_df['remaining'] = edited_df['total'] - edited_df['paid']
        edited_df['status'] = edited_df['remaining'].apply(lambda x: "Paid" if x <= 0 else "Pending")
        edited_df.to_sql('business_deals', conn, if_exists='replace', index=False)
        st.success("Database Updated!")
        st.rerun()
    conn.close()

# --- TAB 3 ---
with tab3:
    st.title("💳 Financial Sheets")
    conn = sqlite3.connect('enterprise.db')
    df = pd.read_sql("SELECT * FROM business_deals", conn)
    conn.close()
    if not df.empty:
        st.subheader("Credit Sheet (Receivables)")
        st.dataframe(df[['client', 'invoice_no', 'team_member', 'total', 'paid', 'remaining', 'status']], use_container_width=True)
        st.subheader("Debit Sheet (Liabilities)")
        st.dataframe(df[['client', 'invoice_no', 'cost', 'paid']], use_container_width=True)

# --- TAB 4 ---
with tab4:
    st.title("📊 Performance Insights")
    conn = sqlite3.connect('enterprise.db')
    df_biz = pd.read_sql("SELECT * FROM business_deals", conn)
    conn.close()
    if not df_biz.empty:
        st.metric("Total Revenue", f"Rs {int(df_biz['total'].sum()):,}")
        fig = px.bar(df_biz, x='invoice_no', y='total', template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
