import json
import os
import streamlit as st

# ---------------------------
# JSON STORAGE HELPERS
# ---------------------------

def load_data(filename):
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            json.dump([], f)
    with open(filename, "r") as f:
        return json.load(f)

def save_data(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


# ---------------------------
# APP UI
# ---------------------------
st.set_page_config(page_title="India Stock Dashboard", layout="wide")
st.title("📈 Indian Stock Portfolio Dashboard")


# ---------------------------
# LOAD DATA
# ---------------------------
portfolio = load_data("portfolio.json")
watchlist = load_data("watchlist.json")


# ---------------------------
# TABS
# ---------------------------
tab1, tab2 = st.tabs(["💼 Portfolio", "👀 Watchlist"])


# ============================================
# TAB 1 ▸ PORTFOLIO
# ============================================
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
        add_button = st.button("Add")

    if add_button and stock:
        portfolio.append({
            "stock": stock.upper(),
            "qty": qty,
            "avg_price": avg_price
        })
        save_data("portfolio.json", portfolio)
        st.success(f"Added {stock} to portfolio! Refresh to view.")

    st.subheader("📋 Your Portfolio Data")

    if len(portfolio) == 0:
        st.info("No stocks in portfolio.")
    else:
        st.table(portfolio)

    # Delete
    st.subheader("🗑 Delete Stock From Portfolio")
    names = [p["stock"] for p in portfolio]
    
    if names:
        stock_to_delete = st.selectbox("Select stock to delete", names)
        if st.button("Delete"):
            portfolio = [p for p in portfolio if p["stock"] != stock_to_delete]
            save_data("portfolio.json", portfolio)
            st.warning(f"{stock_to_delete} deleted. Refresh to view.")


# ============================================
# TAB 2 ▸ WATCHLIST
# ============================================
with tab2:
    st.header("👀 Watchlist")

    st.subheader("Add Stock to Watchlist")

    col1, col2 = st.columns(2)
    with col1:
        watch_stock = st.text_input("Stock Symbol (e.g. RELIANCE)")
    with col2:
        wl_add = st.button("Add to Watchlist")

    if wl_add and watch_stock:
        watchlist.append({"stock": watch_stock.upper()})
        save_data("watchlist.json", watchlist)
        st.success(f"Added {watch_stock} to watchlist! Refresh to view.")

    st.subheader("📋 Watchlist Data")
    st.table(watchlist)

    # Delete watchlist stock
    names2 = [w["stock"] for w in watchlist]
    if names2:
        wl_to_del = st.selectbox("Delete from watchlist", names2)
        if st.button("Delete Watchlist Item"):
            watchlist = [w for w in watchlist if w["stock"] != wl_to_del]
            save_data("watchlist.json", watchlist)
            st.warning(f"{wl_to_del} removed. Refresh to view.")
