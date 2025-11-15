import streamlit as st
import pandas as pd
import yfinance as yf
import streamlit_authenticator as stauth
import yaml

# Load YAML config
with open("config.yaml") as file:
    config = yaml.safe_load(file)

# Initialize authenticator
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    cookie_expiry_days=config['cookie']['expiry_days']
)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status is False:
    st.error("Username/password is incorrect")
elif authentication_status is None:
    st.warning("Please enter your username and password")
elif authentication_status:
    st.success(f"Welcome {name}!")
    authenticator.logout("Logout", "sidebar")

    # Dashboard Tabs
    tabs = ["Portfolio", "Watchlist"]
    selected_tab = st.sidebar.radio("Navigate", tabs)

    if selected_tab == "Portfolio":
        st.title("📈 Portfolio Dashboard")

        if "portfolio" not in st.session_state:
            st.session_state.portfolio = pd.DataFrame(columns=["Stock", "Qty", "Avg Price"])

        with st.expander("➕ Add New Stock"):
            new_stock = st.text_input("Stock Ticker").upper()
            new_qty = st.number_input("Quantity", min_value=1, value=1)
            new_price = st.number_input("Average Price", min_value=0.0, value=0.0)
            if st.button("Add Stock"):
                st.session_state.portfolio = pd.concat(
                    [st.session_state.portfolio,
                     pd.DataFrame([[new_stock, new_qty, new_price]], columns=["Stock", "Qty", "Avg Price"])],
                    ignore_index=True
                )
                st.success(f"Added {new_stock} to portfolio")

        if not st.session_state.portfolio.empty:
            portfolio_df = st.session_state.portfolio.copy()

            def get_current_price(ticker):
                try:
                    return yf.Ticker(ticker).info["regularMarketPrice"]
                except:
                    return None

            portfolio_df["Current Price"] = portfolio_df["Stock"].apply(get_current_price)
            portfolio_df["Current Value"] = portfolio_df["Qty"] * portfolio_df["Current Price"]
            portfolio_df["Invested Value"] = portfolio_df["Qty"] * portfolio_df["Avg Price"]
            portfolio_df["P/L"] = portfolio_df["Current Value"] - portfolio_df["Invested Value"]

            st.dataframe(portfolio_df)

            total_invested = portfolio_df["Invested Value"].sum()
            total_current = portfolio_df["Current Value"].sum()
            total_pl = total_current - total_invested

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Invested", f"₹{total_invested:,.2f}")
            col2.metric("Current Value", f"₹{total_current:,.2f}")
            col3.metric("Unrealized P/L", f"₹{total_pl:,.2f}")

            with st.expander("🗑 Delete Stock"):
                stock_to_delete = st.selectbox("Select Stock to Delete", portfolio_df["Stock"])
                if st.button("Delete Stock"):
                    st.session_state.portfolio = portfolio_df[portfolio_df["Stock"] != stock_to_delete]
                    st.success(f"Deleted {stock_to_delete} from portfolio")

    elif selected_tab == "Watchlist":
        st.title("🔎 Watchlist")
        if "watchlist" not in st.session_state:
            st.session_state.watchlist = []

        new_watch = st.text_input("Add Ticker to Watchlist").upper()
        if st.button("Add to Watchlist") and new_watch:
            if new_watch not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_watch)
                st.success(f"{new_watch} added to watchlist")

        if st.session_state.watchlist:
            watch_data = []
            for ticker in st.session_state.watchlist:
                try:
                    price = yf.Ticker(ticker).info["regularMarketPrice"]
                except:
                    price = None
                watch_data.append({"Stock": ticker, "Current Price": price})
            st.dataframe(pd.DataFrame(watch_data))
