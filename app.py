import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from io import BytesIO

# ------------------- DATABASE -------------------
conn = sqlite3.connect("finance_tracker.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                type TEXT,
                category TEXT,
                amount REAL,
                note TEXT
            )""")
conn.commit()

# ------------------- FUNCTIONS -------------------
def add_transaction(date, type_, category, amount, note):
    c.execute("INSERT INTO transactions (date, type, category, amount, note) VALUES (?, ?, ?, ?, ?)",
              (date, type_, category, amount, note))
    conn.commit()

def get_all_transactions():
    c.execute("SELECT * FROM transactions ORDER BY date DESC")
    return c.fetchall()

def export_excel():
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Transactions")
    return output.getvalue()

# ------------------- STREAMLIT UI -------------------
st.set_page_config(page_title="💰 Personal Finance Tracker", layout="wide")
st.title("💰 Personal Finance Tracker")

menu = ["Add Transaction", "View Transactions", "Analytics"]
choice = st.sidebar.radio("📌 Menu", menu)

if choice == "Add Transaction":
    st.subheader("➕ Add New Transaction")
    date = st.date_input("Date", datetime.today())
    type_ = st.radio("Type", ["Income", "Expense"])
    category = st.text_input("Category (e.g. Food, Rent, Salary)")
    amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    note = st.text_area("Note (Optional)")
    
    if st.button("Save Transaction"):
        add_transaction(str(date), type_, category, amount, note)
        st.success("✅ Transaction Saved Successfully!")

elif choice == "View Transactions":
    st.subheader("📋 All Transactions")
    data = get_all_transactions()
    df = pd.DataFrame(data, columns=["ID", "Date", "Type", "Category", "Amount", "Note"])
    st.dataframe(df, use_container_width=True)

    excel_file = export_excel()
    st.download_button("⬇️ Download as Excel", data=excel_file, file_name="transactions.xlsx")

elif choice == "Analytics":
    st.subheader("📊 Analytics")
    df = pd.read_sql_query("SELECT * FROM transactions", conn)

    if not df.empty:
        income = df[df["type"] == "Income"]["amount"].sum()
        expense = df[df["type"] == "Expense"]["amount"].sum()
        balance = income - expense

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Income", f"Rs {income:,.2f}")
        col2.metric("Total Expense", f"Rs {expense:,.2f}")
        col3.metric("Balance", f"Rs {balance:,.2f}")

        # Pie Chart
        fig1, ax1 = plt.subplots()
        df.groupby("type")["amount"].sum().plot.pie(autopct="%.1f%%", ax=ax1)
        ax1.set_ylabel("")
        st.pyplot(fig1)

        # Category-wise Bar Chart
        fig2, ax2 = plt.subplots()
        df.groupby("category")["amount"].sum().plot(kind="bar", ax=ax2)
        ax2.set_ylabel("Amount")
        st.pyplot(fig2)
    else:
        st.warning("⚠️ No data available. Please add transactions.")