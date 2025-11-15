import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

st.set_page_config(page_title="Indian Stock Dashboard", layout="wide", page_icon="📈")

st.title("📈 Indian Stock Portfolio Dashboard")

# -----------------------------
# SIDEBAR MENU
# -----------------------------
menu = st.sidebar.radio("Navigation", ["Portfolio", "Watchlist", "Analytics"])

# -----------------------------
# PORTFOLIO DATA
# -----------------------------
if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=["Stock", "Qty", "Avg Price"])

# -----------------------------
# PORTFOLIO TAB
# -----------------------------
if menu == "Portfolio":
    st.subheader("Your Portfolio")

    # Metrics cards
    if not st.session_state.portfolio.empty:
        total_invested = (st.session_state.portfolio["Qty"] * st.session_state.portfolio["Avg Price"]).sum()
        
        # Fetch current price
        st.session_state.portfolio["Current Price"] = st.session_state.portfolio["Stock"].apply(
            lambda x: yf.Ticker(x).info.get("regularMarketPrice", 0)
        )
        st.session_state.portfolio["P&L"] = (st.session_state.portfolio["Current Price"] - st.session_state.portfolio["Avg Price"]) * st.session_state.portfolio["Qty"]
        current_value = (st.session_state.portfolio["Current Price"] * st.session_state.portfolio["Qty"]).sum()
        unrealized_pnl = current_value - total_invested

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Invested", f"₹{total_invested:,.2f}")
        col2.metric("Current Value", f"₹{current_value:,.2f}")
        col3.metric("Unrealized P&L", f"₹{unrealized_pnl:,.2f}")

        st.dataframe(st.session_state.portfolio, use_container_width=True)

    # Add new stock
    with st.expander("➕ Add New Stock"):
        with st.form("add_stock_form"):
            stock = st.text_input("Stock Symbol (NSE ticker)")
            qty = st.number_input("Quantity", min_value=1, step=1)
            avg_price = st.number_input("Average Price", min_value=0.01, step=0.01)
            submitted = st.form_submit_button("Add Stock")
            if submitted:
                new_row = pd.DataFrame([[stock, qty, avg_price]], columns=["Stock", "Qty", "Avg Price"])
                st.session_state.portfolio = pd.concat([st.session_state.portfolio, new_row], ignore_index=True)
                st.success(f"{stock} added to portfolio!")

    # Delete stock
    with st.expander("🗑 Delete Stock"):
        if not st.session_state.portfolio.empty:
            stock_to_delete = st.selectbox("Select stock to delete", options=st.session_state.portfolio["Stock"].tolist())
            if st.button("Delete Stock"):
                st.session_state.portfolio = st.session_state.portfolio[st.session_state.portfolio["Stock"] != stock_to_delete]
                st.success(f"{stock_to_delete} deleted!")

# -----------------------------
# WATCHLIST TAB
# -----------------------------
elif menu == "Watchlist":
    st.subheader("Watchlist")
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = pd.DataFrame(columns=["Stock"])

    with st.expander("➕ Add to Watchlist"):
        new_watch = st.text_input("Stock Symbol")
        if st.button("Add to Watchlist"):
            if new_watch and new_watch not in st.session_state.watchlist["Stock"].tolist():
                st.session_state.watchlist = pd.concat([st.session_state.watchlist, pd.DataFrame([[new_watch]], columns=["Stock"])], ignore_index=True)
                st.success(f"{new_watch} added!")

    st.dataframe(st.session_state.watchlist, use_container_width=True)

# -----------------------------
# ANALYTICS TAB
# -----------------------------
elif menu == "Analytics":
    st.subheader("Portfolio Analytics")
    if not st.session_state.portfolio.empty:
        # Pie chart for allocation
        fig = px.pie(st.session_state.portfolio, names="Stock", values="Qty", title="Portfolio Allocation")
        st.plotly_chart(fig, use_container_width=True)

        # P&L distribution
        fig2 = px.bar(st.session_state.portfolio, x="Stock", y="P&L", title="Stock-wise Gain/Loss")
        st.plotly_chart(fig2, use_container_width=True)
