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
                 (id INTEGER PRIMARY KEY, date TEXT, invoice_no TEXT, client TEXT, equipment TEXT, specs TEXT, 
                  unit_price REAL, quantity REAL, close_deal REAL, unit_actual_cost REAL, actual_cost REAL, 
                  paid REAL, remaining REAL, profit REAL, team_member TEXT, status TEXT)''')
    conn.commit()
    conn.close()

init_db()

st.set_page_config(page_title="Hameez Enterprise Hub", layout="wide")

if 'business_df' not in st.session_state:
    conn = sqlite3.connect('enterprise.db')
    st.session_state.business_df = pd.read_sql("SELECT * FROM business_deals", conn)
    conn.close()

tab1, tab2, tab3, tab4 = st.tabs(["🏠 Home Finance", "💼 Business Deals", "💳 Credit/Debit Sheets", "📊 Analytics"])

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
            close_deal = u_price * qty
            actual_cost = unit_actual_cost * qty
            remaining = close_deal - paid
            profit = close_deal - actual_cost
            status = "Paid" if remaining <= 0 else "Pending"
            
            conn = sqlite3.connect('enterprise.db')
            conn.execute("""INSERT INTO business_deals 
                          (date, invoice_no, client, equipment, specs, unit_price, quantity, close_deal, unit_actual_cost, actual_cost, paid, remaining, profit, team_member, status) 
                          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                         (datetime.now().strftime("%Y-%m-%d"), inv_no, client, equipment, specs, u_price, qty, close_deal, unit_actual_cost, actual_cost, paid, remaining, profit, team_member, status))
            conn.commit()
            st.session_state.business_df = pd.read_sql("SELECT * FROM business_deals", conn)
            conn.close()
            st.rerun()

    # 📋 Recent Deals section
    # 📋 Recent Deals section
    st.subheader("📋 Recent Deals")

    # 1. Editor
    editor_result = st.data_editor(
        st.session_state.business_df, 
        use_container_width=True, 
        hide_index=True,
        key="data_editor_main"
    )

    # 2. Logic: Sirf 'remaining' edit hone par update kare
    if "data_editor_main" in st.session_state and st.session_state["data_editor_main"]["edited_rows"]:
        edited_rows = st.session_state["data_editor_main"]["edited_rows"]
        if any('remaining' in row for row in edited_rows.values()):
            edited_df = editor_result.copy()
            edited_df["status"] = edited_df["remaining"].apply(lambda x: "Paid" if x <= 0 else "Pending")
            conn = sqlite3.connect('enterprise.db')
            edited_df.to_sql('business_deals', conn, if_exists='replace', index=False)
            conn.close()
            st.session_state.business_df = edited_df
            st.rerun()
    
    # 3. Highlight Function
    def highlight_remaining(val):
        return 'background-color: #ff4b4b' if isinstance(val, (int, float)) and val > 0 else ''

    # 4. Display Table: Format aur Button Logic
    st.subheader("📋 Records & Print")
    
    # Hum yahan loop use kar rahe hain taake har row ke sath button ho
    for i, row in editor_result.iterrows():
        cols = st.columns([0.9, 0.1])
        
        # Table row ko display karne ke liye hum temporary dataframe bana rahe hain
        row_df = pd.DataFrame([row])
        st_styled = row_df.style.format({
            "close_deal": "{:.0f}", "paid": "{:.0f}", "remaining": "{:.0f}", 
            "unit_price": "{:.0f}", "actual_cost": "{:.0f}", "profit": "{:.0f}", "quantity": "{:.0f}"
        }).map(highlight_remaining, subset=['remaining'])
        
        with cols[0]:
            st.dataframe(st_styled, use_container_width=True, hide_index=True)
            
        with cols[1]:
            st.write("###") # Thoda gap dene ke liye
            if st.button("🖨️ PDF", key=f"print_{i}"):
                # Yahan aapka PDF function call hoga
                # generate_pdf(row) 
                st.info(f"Generating: {row['invoice_no']}")
                
        st.divider()    
          
# Add a newline here before starting the next tab
with tab3:
    st.title("💳 Financial Sheets")
    if not st.session_state.business_df.empty:
        st.dataframe(st.session_state.business_df, use_container_width=True)
with tab4:
    st.title("📊 Performance Insights")
    if not st.session_state.business_df.empty:
        st.metric("Total Revenue", f"Rs {int(st.session_state.business_df['close_deal'].sum()):,}")
        fig = px.bar(st.session_state.business_df, x='invoice_no', y='close_deal', template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
