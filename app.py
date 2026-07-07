import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from fpdf import FPDF
from datetime import datetime

# --- SUPABASE SETUP ---
# Streamlit Secrets mein set karein ya yahan direct paste karein
SUPABASE_URL = st.secrets["SUPABASE_URL"] 
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Hameez Enterprise Hub", layout="wide")

# CSS
st.markdown("""<style>.stApp {background-color: #05070a;} h1, h2 {color: #00f2ff !important;}</style>""", unsafe_allow_html=True)

# --- PDF FUNCTION ---
def download_pdf(row):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "HAMEEZ ENTERPRISE INVOICE", 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    for col, val in row.items():
        pdf.cell(0, 10, f"{col.upper()}: {val}", 0, 1)
    return pdf.output(dest='S').encode('latin-1')

tab1, tab2, tab3, tab4 = st.tabs(["🏠 Home Finance", "💼 Business Deals", "💳 Credit/Debit Sheets", "📊 Analytics"])

# --- TAB 1: Home Finance ---
with tab1:
    st.title("🏡 Home Finance Tracker")
    # Fetch Home Finance
    res_home = supabase.table("home_finance").select("*").execute()
    df_home = pd.DataFrame(res_home.data)
    
    with st.expander("➕ Add Home Transaction"):
        with st.form("home_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            recipient = col_a.selectbox("Who received it?", ["Anoushay", "Hameez", "Talha", "Self", "General House", "Sent to Home"])
            amount = col_b.number_input("Amount (Rs)", min_value=0, step=1)
            if st.form_submit_button("Update Home Finance"):
                supabase.table("home_finance").insert({"recipient": recipient, "amount": amount}).execute()
                st.rerun()
    st.dataframe(df_home, use_container_width=True)

# --- TAB 2: Business Deals ---
with tab2:
    st.title("➕ Register & Manage Medical Deal")
    with st.form("biz_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        doc_type = c1.selectbox("Type", ["Invoice", "Quotation"])
        inv_no = c2.text_input("Invoice No")
        client = c3.text_input("Client Name")
        specs = st.text_input("SPECS")
        c4, c5, c6 = st.columns(3)
        qty = c4.number_input("QUANTITY", min_value=0)
        u_price = c5.number_input("PER UNIT PRICE", min_value=0)
        cost = c6.number_input("Actual Cost", min_value=0)
        paid = st.number_input("Payment Paid", min_value=0)
        
        if st.form_submit_button("Log Deal"):
            total = qty * u_price
            rem = total - paid
            supabase.table("business_deals").insert({
                "date": datetime.now().strftime("%Y-%m-%d"), "client": client, "invoice_no": inv_no,
                "specs": specs, "quantity": qty, "unit_price": u_price, "total": total,
                "cost": cost, "paid": paid, "remaining": rem, "type": doc_type
            }).execute()
            st.rerun()

    res_biz = supabase.table("business_deals").select("*").execute()
    df_biz = pd.DataFrame(res_biz.data)
    st.dataframe(df_biz, use_container_width=True)

# --- TAB 3: Credit/Debit Sheets ---
with tab3:
    st.title("💳 Credit & Debit Records")
    if not df_biz.empty:
        st.subheader("Credit Sheet (Receivables)")
        st.dataframe(df_biz[['client', 'invoice_no', 'total', 'paid', 'remaining']], use_container_width=True)
        
        st.subheader("Debit Sheet (Liabilities)")
        st.dataframe(df_biz[['client', 'invoice_no', 'total', 'paid', 'remaining']], use_container_width=True)

        selected_inv = st.selectbox("Select Invoice No to Download", df_biz['invoice_no'].unique())
        if st.button("Generate PDF"):
            row = df_biz[df_biz['invoice_no'] == selected_inv].iloc[0]
            st.download_button("Click to Download", download_pdf(row), f"{selected_inv}.pdf", "application/pdf")

# --- TAB 4: Analytics ---
with tab4:
    st.title("📊 Performance Insights")
    if not df_biz.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Revenue", f"Rs {df_biz['total'].sum():,}")
        col2.metric("Total Profit", f"Rs {(df_biz['total'] - df_biz['cost']).sum():,}")
        col3.metric("Outstanding", f"Rs {df_biz['remaining'].sum():,}")
        
        fig = px.bar(df_biz, x='invoice_no', y=['cost', 'total'], barmode='group', template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
