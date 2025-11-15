import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import json
import os


# ---------------------------------------
# LOAD AUTH CONFIG
# ---------------------------------------
def load_config():
    with open("config.yaml", "r") as file:
        return yaml.load(file, Loader=SafeLoader)


config = load_config()

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config.get('preauthorized')
)


# ---------------------------------------
# LOGIN UI
# ---------------------------------------
st.set_page_config(page_title="Indian Stock Dashboard", layout="wide")

name, auth_status, username = authenticator.login("Login", "main")

if auth_status is False:
    st.error("Invalid username or password")

elif auth_status is None:
    st.warning("Please enter your username and password")


# ---------------------------------------
# IF LOGGED IN — SHOW DASHBOARD
# ---------------------------------------
if auth_status:

    # Logout button
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"👤 Logged in as: **{name}**")

    st.title("📈 Indian Stock Portfolio Dashboard")

    # ---------------------------------------
    # JSON DATA HELPERS
    # ---------------------------------------
    def load_json(filename):
        if not os.path.exists(filename):
            with open(filename, "w") as f:
                json.dump([], f)
        with open(filename, "r") as f:
            return json.load(f)

    def save_json(filename, data):
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

    portfolio = load_json("portfolio.json")
    watchlist = load_json("watchlist.json")

    # ---------------------------------------
    # TABS
    # ---------------------------------------
    tab1, tab2 = st.tabs(["💼 Portfolio", "👀 Watchlist"])

    # ============================================
    # PORTFOLIO TAB
    # ============================================
    with tab1:
        st.header("💼 Your Portfolio")

        st.subheader("Add a New Stock")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            stock = st.text_input("Stock Symbol (e.g. TATAPOWER)")
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
            save_json("portfolio.json", portfolio)
            st.success(f"{stock.upper()} added to portfolio! Refresh to view.")

        st.subheader("📋 Portfolio Data")

        if len(portfolio) == 0:
            st.info("No stocks in portfolio.")
        else:
            st.table(portfolio)

        st.subheader("🗑 Delete Stock")

        stock_names = [p["stock"] for p in portfolio]

        if stock_names:
            delete_name = st.selectbox("Choose stock to delete", stock_names)
            if st.button("Delete Stock"):
                portfolio = [p for p in portfolio if p["stock"] != delete_name]
                save_json("portfolio.json", portfolio)
                st.warning(f"{delete_name} removed. Refresh to view.")

    # ============================================
    # WATCHLIST TAB
    # ============================================
    with tab2:
        st.header("👀 Watchlist")

        st.subheader("Add Stock to Watchlist")

        col1, col2 = st.columns(2)
        with col1:
            watch_stock = st.text_input("Stock (e.g. RELIANCE)")
        with col2:
            add_wl = st.button("Add to Watchlist")

        if add_wl and watch_stock:
            watchlist.append({"stock": watch_stock.upper()})
            save_json("watchlist.json", watchlist)
            st.success(f"{watch_stock.upper()} added to watchlist!")

        st.subheader("📋 Watchlist Data")
        st.table(watchlist)

        # Delete watchlist
        wl_names = [w["stock"] for w in watchlist]

        if wl_names:
            wl_del = st.selectbox("Delete watchlist item", wl_names)
            if st.button("Delete Watchlist Stock"):
                watchlist = [w for w in watchlist if w["stock"] != wl_del]
                save_json("watchlist.json", watchlist)
                st.warning(f"{wl_del} removed.")


