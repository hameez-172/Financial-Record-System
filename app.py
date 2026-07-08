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
    # Table structure updated with requested columns
    c.execute('''CREATE TABLE IF NOT EXISTS business_deals 
                 (id INTEGER PRIMARY KEY, date TEXT, invoice_no TEXT, client TEXT, equipment TEXT, specs TEXT, 
                  unit_price REAL, total REAL, unit_actual_cost REAL, cost REAL, paid REAL, 
                  remaining REAL, team_member TEXT, status TEXT)''')
    conn.commit()
    conn.close()

init_db()

st.set_page_config(page_title="Hameez Enterprise Hub", layout="wide")

if 'business_df' not in st.session_state:
    conn = sqlite3.connect('enterprise.db')
    st.session_state.business_df = pd.read_sql("SELECT * FROM business_deals", conn)
    conn.close()

tab1, tab2, tab3, tab4 = st.tabs(["🏠 Home Finance", "💼 Business Deals", "💳 Credit/Debit Sheets", "📊 Analytics"])

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
            conn.execute("""INSERT INTO business_deals 
                          (date, invoice_no, client, equipment, specs, unit_price, total, unit_actual_cost, cost, paid, remaining, team_member, status) 
                          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                         (datetime.now().strftime("%Y-%m-%d"), inv_no, client, equipment, specs, u_price, total, unit_actual_cost, actual_cost, paid, remaining, team_member, status))
            conn.commit()
            st.session_state.business_df = pd.read_sql("SELECT * FROM business_deals", conn)
            conn.close()
            st.rerun()

    st.subheader("📋 Recent Deals")
    
    # Requirement ke mutabiq Column Order
    cols_order = ['date', 'invoice_no', 'client', 'equipment', 'specs', 'unit_price', 'total', 'unit_actual_cost', 'cost', 'paid', 'remaining', 'team_member', 'status']
    
    edited_df = st.data_editor(
        st.session_state.business_df[cols_order], 
        use_container_width=True, 
        hide_index=True
    )

    if not edited_df.equals(st.session_state.business_df[cols_order]):
        edited_df["remaining"] = edited_df["cost"] - edited_df["paid"]
        edited_df["status"] = edited_df["remaining"].apply(lambda x: "Paid" if x <= 0 else "Pending")
        
        st.session_state.business_df.update(edited_df)
        conn = sqlite3.connect('enterprise.db')
        edited_df.to_sql('business_deals', conn, if_exists='replace', index=False)
        conn.close()
        st.rerun()

    st.dataframe(edited_df.style.format({
        "total": "{:.0f}", "paid": "{:.0f}", "remaining": "{:.0f}", "cost": "{:.0f}", "unit_price": "{:.0f}", "unit_actual_cost": "{:.0f}"
    }), use_container_width=True)

# Tabs 3 and 4...
with tab3:
    st.title("💳 Financial Sheets")
    df = st.session_state.business_df
    if not df.empty:
        st.dataframe(df[cols_order], use_container_width=True)

with tab4:
    st.title("📊 Performance Insights")
    df_biz = st.session_state.business_df
    if not df_biz.empty:
        st.metric("Total Revenue", f"Rs {int(df_biz['total'].sum()):,}")
        st.plotly_chart(px.bar(df_biz, x='invoice_no', y='total', template="plotly_dark"), use_container_width=True)
