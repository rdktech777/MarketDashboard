import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import json
import os
import pandas as pd
import yfinance as yf
import plotly.express as px

# -----------------------------
# Load Authentication Config
# -----------------------------
with open("config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    credentials=config['credentials'],
    cookie_name=config['cookie']['name'],
    key=config['cookie']['key'],
    cookie_expiry_days=config['cookie']['expiry_days']
)

name, auth_status, username = authenticator.login(
    form_name="Login",
    location="main"
)

# -----------------------------
# Handle login states
# -----------------------------
if auth_status is False:
    st.error("❌ Incorrect username or password.")
elif auth_status is None:
    st.warning("⚠️ Please enter your login details.")
elif auth_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"👤 Logged in as: **{username}**")

    # -----------------------------
    # JSON Data Handling
    # -----------------------------
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
    st.title("📊 Indian Stock Portfolio Dashboard")

    tab1, tab2, tab3 = st.tabs(["💼 Portfolio", "👀 Watchlist", "📈 Market Charts"])

    # -----------------------------
    # TAB 1 — PORTFOLIO
    # -----------------------------
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
            df_portfolio = pd.DataFrame(portfolio)
            st.table(df_portfolio)

        st.subheader("🗑 Remove a Stock")
        if len(portfolio) > 0:
            names = [p["stock"] for p in portfolio]
            del_pick = st.selectbox("Select stock", names)
            if st.button("Delete Stock"):
                portfolio = [p for p in portfolio if p["stock"] != del_pick]
                save_data("portfolio.json", portfolio)
                st.warning(f"{del_pick} deleted.")

    # -----------------------------
    # TAB 2 — WATCHLIST
    # -----------------------------
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
        if len(watchlist) == 0:
            st.info("Add stocks to your watchlist.")
        else:
            df_watch = pd.DataFrame(watchlist)
            st.table(df_watch)

        if len(watchlist) > 0:
            names = [w["stock"] for w in watchlist]
            del_watch = st.selectbox("Remove watchlist item", names)
            if st.button("Delete Watchlist Item"):
                watchlist = [w for w in watchlist if w["stock"] != del_watch]
                save_data("watchlist.json", watchlist)
                st.warning(f"{del_watch} removed.")

    # -----------------------------
    # TAB 3 — STOCK MARKET CHARTS
    # -----------------------------
    with tab3:
        st.header("📈 Live Market Charts")

        chart_sym = st.text_input("Enter Stock Symbol for Chart (e.g., RELIANCE)")

        if st.button("Load Chart") and chart_sym:
            try:
                data = yf.download(chart_sym + ".NS", period="6mo")
                fig = px.line(data, x=data.index, y="Close", title=f"{chart_sym.upper()} — 6 Months Price Trend")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Could not fetch chart data. Error: {str(e)}")
