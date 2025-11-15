import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import json
import os
import pandas as pd
import yfinance as yf
import plotly.express as px

# ---------------------------------------------------------
# Load Authentication Config
# ---------------------------------------------------------
with open("config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

name, auth_status, username = authenticator.login("Login", "main")

# ---------------------------------------------------------
# Login Logic
# ---------------------------------------------------------
if auth_status == False:
    st.error("Username or password is incorrect.")

elif auth_status == None:
    st.warning("Please enter your login details.")

elif auth_status:

    # Sidebar user info
    authenticator.logout("Logout", "sidebar")
    st.sidebar.write(f"👤 Logged in as **{name}**")

    # ---------------------------------------------------------
    # JSON Data Handling
    # ---------------------------------------------------------
    def load_data(filename):
        if not os.path.exists(filename):
            with open(filename, "w") as f:
                json.dump([], f)
        with open(filename, "r") as f:
            return json.load(f)

    def save_data(filename, data):
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

    portfolio = load_data("portfolio.json")
    watchlist = load_data("watchlist.json")

    st.set_page_config(page_title="Indian Stock Dashboard", layout="wide")
    st.title("📊 Indian Stock Dashboard")

    tab1, tab2, tab3 = st.tabs(["💼 Portfolio", "👀 Watchlist", "📈 Market Charts"])

    # ---------------------------------------------------------
    # TAB 1 — PORTFOLIO
    # ---------------------------------------------------------
    with tab1:
        st.header("💼 Portfolio Manager")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            stock = st.text_input("Stock Symbol (e.g., TCS)")
        with col2:
            qty = st.number_input("Quantity", min_value=1, value=1)
        with col3:
            avg_price = st.number_input("Average Buy Price", min_value=1.0)
        with col4:
            add_btn = st.button("Add Stock")

        if add_btn and stock:
            portfolio.append({
                "stock": stock.upper(),
                "qty": qty,
                "avg_price": avg_price
            })
            save_data("portfolio.json", portfolio)
            st.success(f"{stock.upper()} added to portfolio.")

        st.subheader("📋 Current Portfolio")
        if len(portfolio) == 0:
            st.info("Add stocks to build your portfolio.")
        else:
            df = pd.DataFrame(portfolio)
            st.table(df)

        st.subheader("🗑 Remove a Stock")
        if len(portfolio) > 0:
            names = [p["stock"] for p in portfolio]
            del_pick = st.selectbox("Select stock", names)
            if st.button("Delete"):
                portfolio = [p for p in portfolio if p["stock"] != del_pick]
                save_data("portfolio.json", portfolio)
                st.warning(f"{del_pick} deleted.")

    # ---------------------------------------------------------
    # TAB 2 — WATCHLIST
    # ---------------------------------------------------------
    with tab2:
        st.header("👀 Watchlist Manager")

        col1, col2 = st.columns(2)
        with col1:
            watch_sym = st.text_input("Stock Symbol")
        with col2:
            wl_btn = st.button("Add to Watchlist")

        if wl_btn and watch_sym:
            watchlist.append({"stock": watch_sym.upper()})
            save_data("watchlist.json", watchlist)
            st.success(f"{watch_sym.upper()} added to watchlist.")

        st.subheader("📋 Watchlist")
        st.table(watchlist)

        if len(watchlist) > 0:
            names = [w["stock"] for w in watchlist]
            del_watch = st.selectbox("Remove watchlist item", names)
            if st.button("Delete Watchlist Item"):
                watchlist = [w for w in watchlist if w["stock"] != del_watch]
                save_data("watchlist.json", watchlist)
                st.warning(f"{del_watch} removed.")

    # ---------------------------------------------------------
    # TAB 3 — STOCK MARKET CHARTS
    # ---------------------------------------------------------
    with tab3:
        st.header("📈 Live Market Charts")

        chart_sym = st.text_input("Enter Stock Symbol for Chart (example: RELIANCE)")

        if st.button("Load Chart") and chart_sym:
            try:
                data = yf.download(chart_sym + ".NS", period="6mo")
                fig = px.line(data, x=data.index, y="Close", title=f"{chart_sym.upper()} — 6 Months Price Trend")
                st.plotly_chart(fig, use_container_width=True)
            except:
                st.error("Could not fetch chart data. Check the symbol or network.")
