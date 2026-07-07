import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Page Config
st.set_page_config(page_title="Hameez Finance Hub", layout="wide", page_icon="💰")

# 2. Professional CSS Styling (Colorful & Clean)
st.markdown("""
    <style>
    .main {background-color: #0b0e14;}
    .stMetric {background-color: #1e1e24; padding: 20px; border-radius: 15px; border: 1px solid #333;}
    h1, h2, h3 {color: #e0e0e0 !important;}
    .css-1r6slb0 {padding: 1rem;}
    </style>
""", unsafe_allow_html=True)

# 3. Dummy Data (Yahan hum baad mein Google Sheets connect karenge)
data = {
    'Date': ['2026-07-01', '2026-07-02', '2026-07-03', '2026-07-04'],
    'Description': ['Client Payment', 'Electricity Bill', 'Home Transfer', 'University Fee'],
    'Category': ['Business', 'Bills', 'Personal', 'Fees'],
    'Type': ['Income', 'Expense', 'Expense', 'Expense'],
    'Amount': [85000, 12000, 25000, 15000]
}
df = pd.DataFrame(data)

# 4. Sidebar - Data Entry Form (Professional Entry)
with st.sidebar:
    st.header("➕ Add Transaction")
    with st.form("entry_form"):
        desc = st.text_input("Description")
        cat = st.selectbox("Category", ["Business", "Personal", "Bills", "Fees"])
        t_type = st.radio("Type", ["Income", "Expense"], horizontal=True)
        amt = st.number_input("Amount (Rs)", min_value=0)
        submitted = st.form_submit_button("Save Record")
        if submitted:
            st.success("Record Added!")

# 5. Dashboard Top Metrics
st.title("📊 Financial Intelligence Hub")
col1, col2, col3, col4 = st.columns(4)

total_income = df[df['Type']=='Income']['Amount'].sum()
total_exp = df[df['Type']=='Expense']['Amount'].sum()

col1.metric("Total Revenue", f"Rs {total_income:,}", delta="12%")
col2.metric("Total Expenses", f"Rs {total_exp:,}", delta="-5%", delta_color="inverse")
col3.metric("Savings", f"Rs {total_income - total_exp:,}")
col4.metric("Transactions", len(df))

# 6. Charts (Responsive)
col_a, col_b = st.columns([2, 1])

with col_a:
    st.subheader("Cash Flow Trend")
    fig = px.bar(df, x='Date', y='Amount', color='Category', barmode='group', template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.subheader("Expense Split")
    fig2 = px.pie(df, values='Amount', names='Category', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(fig2, use_container_width=True)

# 7. Detailed Table
st.subheader("📝 Recent Transactions")
st.dataframe(df, use_container_width=True)