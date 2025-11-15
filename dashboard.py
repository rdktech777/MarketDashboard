import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import json
import os

# ---------------------------------------------------------
# LOAD CONFIG
# ---------------------------------------------------------
with open("config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

st.set_page_config(page_title="India Stock Dashboard", layout="wide")

name, auth_status, username = authenticator.login("Login", "main")

if auth_status == False:
    st.error("Username or password is incorrect")

elif auth_status == None:
    st.warning("Please enter your username and password")

elif auth_status:
    # ---------------------------------------------------------
    # SUCCESSFUL LOGIN → LOAD APP
    # ---------------------------------------------------------
    authenticator.logout("Logout", "sidebar")
    st.sidebar.write(f"👤 Logged in as **{name}**")

    # ---------------------------------------------------------
    # JSON STORAGE HELPERS
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

    # ---------------------------------------------------------
    # LOAD DATA
    # ---------------------------------------------------------
    portfolio = load_data("portfolio.json")
    watchlist = load_data("watchlist.json")

    # ---------------------------------------------------------
    # APP UI
    # ---------------------------------------------------------
    st.title("📈 Indian Stock Portfolio Dashboard")

    tab1, tab2 = st.tabs(["💼 Portfolio", "👀 Watchlist"])

    # =========================================================
    # TAB 1: PORTFOLIO
    # =========================================================
    with tab1:
        st.header("💼 Your Portfolio")

        st.subheader("Add Stock to Portfolio")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            stock = st.text_input("Stock Name (e.g. TATAMOTORS)")
        with col2:
            qty = st.number_input("Quantity", min_value=1, value=1)
        with col3:
            avg_price = st.number_input("Average Buy Price", min_value=1.0, value=1.0)
        with col4:
            add_btn = st.button("Add Stock")

        if add_btn and stock:
            portfolio.append({
                "stock": stock.upper(),
                "qty": qty,
                "avg_price": avg_price
            })
            save_data("portfolio.json", portfolio)
            st.success(f"Added {stock.upper()} to your portfolio!")
            st.rerun()

        st.subheader("📋 Current Portfolio")

        if len(portfolio) == 0:
            st.info("No stocks added yet.")
        else:
            st.table(portfolio)

        st.subheader("🗑 Delete Stock")
        names = [p["stock"] for p in portfolio]

        if names:
            del_name = st.selectbox("Select stock to delete", names)
            if st.button("Delete Stock"):
                portfolio = [p for p in portfolio if p["stock"] != del_name]
                save_data("portfolio.json", portfolio)
                st.warning(f"{del_name} deleted from portfolio.")
                st.rerun()

    # =========================================================
    # TAB 2: WATCHLIST
    # =========================================================
    with tab2:
        st.header("👀 Watchlist")

        st.subheader("Add Stock to Watchlist")

        col1, col2 = st.columns(2)
        with col1:
            wl_stock = st.text_input("Stock Symbol (e.g. RELIANCE)")
        with col2:
            wl_btn = st.button("Add to Watchlist")

        if wl_btn and wl_stock:
            watchlist.append({"stock": wl_stock.upper()})
            save_data("watchlist.json", watchlist)
            st.success(f"Added {wl_stock.upper()} to watchlist!")
            st.rerun()

        st.subheader("📋 Watchlist Data")
        st.table(watchlist)

        names_wl = [w["stock"] for w in watchlist]

        if names_wl:
            del_wl = st.selectbox("Delete from watchlist", names_wl)
            if st.button("Delete Watchlist Item"):
                watchlist = [w for w in watchlist if w["stock"] != del_wl]
                save_data("watchlist.json", watchlist)
                st.warning(f"{del_wl} removed from watchlist.")
                st.rerun()
