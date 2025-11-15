# dashboard_pro.py
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import json
import os
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from io import StringIO, BytesIO

# -------------------------
# CONFIG / AUTH
# -------------------------
@st.cache_data(ttl=3600)
def load_config():
    with open("config.yaml", "r") as f:
        return yaml.load(f, Loader=SafeLoader)

config = load_config()

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config.get('preauthorized')
)

st.set_page_config(page_title="STOCKS MONITORING DASHBOARD WITH REALTIME DATA FEED", layout="wide")
name, auth_status, username = authenticator.login("Login", "main")

if auth_status is False:
    st.error("Invalid username / password")
    st.stop()
elif auth_status is None:
    st.warning("Please enter username and password")
    st.stop()

# -------------------------
# Helper: JSON storage
# -------------------------
def ensure_file(fn):
    if not os.path.exists(fn):
        with open(fn, "w") as f:
            json.dump([], f)

def load_json(fn):
    ensure_file(fn)
    with open(fn, "r") as f:
        return json.load(f)

def save_json(fn, data):
    with open(fn, "w") as f:
        json.dump(data, f, indent=4)

# files
PORTF_FILE = "portfolio.json"
WATCH_FILE = "watchlist.json"
ensure_file(PORTF_FILE)
ensure_file(WATCH_FILE)

# -------------------------
# Data: load
# -------------------------
portfolio = load_json(PORTF_FILE)  # list of dicts: stock, qty, avg_price, exchange(optional)
watchlist = load_json(WATCH_FILE)  # list of dicts: stock, exchange(optional), alert_price(optional)

# -------------------------
# Utilities: ticker normalization & price fetch
# -------------------------
def normalize_ticker(ticker: str, exchange_hint: str = "NSE"):
    """Return ticker string compatible with yfinance. For NSE use .NS suffix"""
    t = ticker.strip().upper()
    # if user already gave suffix, return as-is
    if "." in t:
        return t
    if exchange_hint and exchange_hint.upper() in ("NSE", "NIFTY", "BSE"):
        if exchange_hint.upper() == "BSE":
            # BSE tickers aren't reliably supported on yfinance; user should provide full ticker
            return t
        return f"{t}.NS"
    return f"{t}.NS"

@st.cache_data(ttl=30)
def fetch_quote(ticker: str):
    """Return (symbol, current_price, previous_close, timestamp) or (symbol, None, None, None) on error"""
    try:
        t = yf.Ticker(ticker)
        # fetch last close using history to avoid flaky info fields
        hist = t.history(period="5d", interval="1d")
        if hist is None or hist.empty:
            return ticker, None, None, None
        last = hist["Close"].iloc[-1]
        prev = hist["Close"].iloc[-2] if len(hist) >= 2 else last
        ts = hist.index[-1].to_pydatetime()
        return ticker, float(last), float(prev), ts
    except Exception:
        return ticker, None, None, None

@st.cache_data(ttl=300)
def fetch_history(ticker: str, period="6mo", interval="1d"):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period, interval=interval)
        return hist
    except Exception:
        return pd.DataFrame()

# -------------------------
# Logged-in UI
# -------------------------
authenticator.logout("Logout", "sidebar")
st.sidebar.success(f"👤 Logged in as: **{name}**")
st.title("📈 Professional Indian Stock Dashboard")

# Sidebar controls
with st.sidebar.expander("Portfolio Controls"):
    st.write("Import / Export")
    col_im, col_ex = st.columns(2)
    with col_im:
        uploaded = st.file_uploader("Import portfolio JSON", type=["json"])
        if uploaded:
            try:
                data = json.load(uploaded)
                save_json(PORTF_FILE, data)
                st.success("Portfolio imported. Refreshing...")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Invalid JSON: {e}")
    with col_ex:
        if st.button("Export portfolio JSON"):
            with open(PORTF_FILE, "r") as f:
                btn = st.download_button("Download portfolio.json", f.read(), file_name="portfolio.json", mime="application/json")

    st.markdown("---")
    st.write("Quick actions")
    if st.button("Clear portfolio"):
        save_json(PORTF_FILE, [])
        st.experimental_rerun()

with st.sidebar.expander("Watchlist Controls"):
    if st.button("Export watchlist"):
        with open(WATCH_FILE, "r") as f:
            st.download_button("Download watchlist.json", f.read(), file_name="watchlist.json", mime="application/json")
    if st.button("Clear watchlist"):
        save_json(WATCH_FILE, [])
        st.experimental_rerun()

# Tabs for main area
tab_overview, tab_portfolio, tab_watch, tab_tools = st.tabs(["Overview", "Portfolio", "Watchlist", "Tools"])

# -------------------------
# Overview tab
# -------------------------
with tab_overview:
    st.header("Portfolio Overview")

    # Compute live prices for portfolio
    if portfolio:
        df_rows = []
        total_invested = 0.0
        total_market = 0.0
        for p in portfolio:
            symbol = p.get("stock")
            qty = p.get("qty", 0)
            avg = p.get("avg_price", 0.0)
            yf_sym = normalize_ticker(symbol, p.get("exchange", "NSE"))
            tk, price, prev, ts = fetch_quote(yf_sym)
            invested = qty * avg
            market = qty * (price if price is not None else 0.0)
            pl = market - invested
            pl_pct = (pl / invested * 100) if invested else 0.0
            total_invested += invested
            total_market += market
            df_rows.append({
                "stock": symbol.upper(),
                "yf_ticker": yf_sym,
                "qty": qty,
                "avg_price": avg,
                "invested": round(invested,2),
                "current_price": round(price,2) if price else None,
                "market_value": round(market,2),
                "unrealized_pl": round(pl,2),
                "pl_pct": round(pl_pct,2)
            })
        df_port = pd.DataFrame(df_rows).sort_values("market_value", ascending=False)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Invested (₹)", f"{total_invested:,.2f}")
        col2.metric("Total Market Value (₹)", f"{total_market:,.2f}")
        col3.metric("Unrealized P&L (₹)", f"{(total_market-total_invested):,.2f}")
        st.dataframe(df_port, use_container_width=True)

        # Allocation pie chart
        st.subheader("Allocation")
        fig1, ax1 = plt.subplots()
        # avoid zero sum
        vals = df_port["market_value"].replace(0, 0.0001)
        ax1.pie(vals, labels=df_port["stock"], autopct="%1.1f%%", startangle=90)
        ax1.axis("equal")
        st.pyplot(fig1)

        # Portfolio performance over time (using historical closes)
        st.subheader("Portfolio Value Over Time (approx)")
        # build time series by summing qty * close for each stock for the last 6 months
        end = datetime.now()
        start = end - timedelta(days=180)
        dates = pd.date_range(start=start.date(), end=end.date(), freq="1D")
        portfolio_series = pd.Series(0.0, index=dates)
        for p in portfolio:
            sym = normalize_ticker(p["stock"], p.get("exchange","NSE"))
            hist = fetch_history(sym, period="6mo", interval="1d")
            if hist is None or hist.empty:
                continue
            # align to our date index
            hist_close = hist["Close"].reindex(dates, method="ffill").fillna(method="ffill").fillna(0)
            portfolio_series = portfolio_series + hist_close * p.get("qty",0)
        if portfolio_series.sum() == 0:
            st.info("Not enough historical data to plot performance.")
        else:
            fig2, ax2 = plt.subplots()
            ax2.plot(portfolio_series.index, portfolio_series.values)
            ax2.set_title("Portfolio Value (last 6 months)")
            ax2.set_ylabel("Value (₹)")
            st.pyplot(fig2)
    else:
        st.info("Your portfolio is empty. Add stocks in the Portfolio tab.")

# -------------------------
# Portfolio tab: detailed CRUD + per-stock charting + export
# -------------------------
with tab_portfolio:
    st.header("Portfolio Manager")

    # Add new stock form
    with st.form("add_stock_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([2,1,1,1])
        with c1:
            new_stock = st.text_input("Stock symbol (e.g. TATAPOWER)")
        with c2:
            new_qty = st.number_input("Quantity", min_value=1, value=1)
        with c3:
            new_avg = st.number_input("Avg buy price (₹)", min_value=0.01, value=1.0, format="%.2f")
        with c4:
            new_exch = st.selectbox("Exchange", options=["NSE","BSE"], index=0)
        submitted = st.form_submit_button("Add / Update")
        if submitted and new_stock:
            # if exists update qty & avg (append as new entry otherwise)
            found = False
            for entry in portfolio:
                if entry["stock"].strip().upper() == new_stock.strip().upper():
                    # update by averaging weighted avg
                    old_qty = entry.get("qty",0)
                    old_avg = entry.get("avg_price",0)
                    total_qty = old_qty + new_qty
                    if total_qty == 0:
                        entry["avg_price"] = new_avg
                    else:
                        entry["avg_price"] = round((old_avg*old_qty + new_avg*new_qty)/total_qty, 2)
                    entry["qty"] = total_qty
                    entry["exchange"] = new_exch
                    found = True
                    break
            if not found:
                portfolio.append({"stock": new_stock.strip().upper(), "qty": new_qty, "avg_price": float(new_avg), "exchange": new_exch})
            save_json(PORTF_FILE, portfolio)
            st.success(f"{new_stock.strip().upper()} added/updated.")
            st.experimental_rerun()

    # Current portfolio table & actions
    st.subheader("Current Holdings")
    if portfolio:
        df = pd.DataFrame(portfolio)
        st.dataframe(df, use_container_width=True)
        # Select a stock to view history & remove
        sel = st.selectbox("Select a holding to inspect", [p["stock"] for p in portfolio])
        if sel:
            entry = next((p for p in portfolio if p["stock"]==sel), None)
            if entry:
                st.write("Holding details:", entry)
                sym = normalize_ticker(entry["stock"], entry.get("exchange","NSE"))
                ticker, price, prev, ts = fetch_quote(sym)
                st.write(f"Live: {price}   Prev: {prev}   As of: {ts}")
                # History plot
                hist = fetch_history(sym, period="1y", interval="1d")
                if not hist.empty:
                    fig, ax = plt.subplots()
                    ax.plot(hist.index, hist["Close"])
                    ax.set_title(f"{sel} - 1 year close")
                    ax.set_ylabel("Price (₹)")
                    st.pyplot(fig)
                if st.button("Remove holding"):
                    portfolio = [p for p in portfolio if p["stock"] != sel]
                    save_json(PORTF_FILE, portfolio)
                    st.warning(f"{sel} removed.")
                    st.experimental_rerun()
    else:
        st.info("No holdings present.")

    # Export CSV of current portfolio valuations (live)
    if st.button("Export portfolio valuations CSV"):
        # build valuations
        rows = []
        for p in portfolio:
            yf_sym = normalize_ticker(p["stock"], p.get("exchange","NSE"))
            _, price, _, _ = fetch_quote(yf_sym)
            rows.append({
                "stock": p["stock"],
                "qty": p["qty"],
                "avg_price": p["avg_price"],
                "current_price": price,
                "invested": p["qty"]*p["avg_price"],
                "market_value": p["qty"]*(price if price else 0)
            })
        dfv = pd.DataFrame(rows)
        csv = dfv.to_csv(index=False).encode()
        st.download_button("Download valuations CSV", data=csv, file_name="portfolio_valuations.csv", mime="text/csv")

# -------------------------
# Watchlist tab: add, remove, alerts
# -------------------------
with tab_watch:
    st.header("Watchlist")

    col_a, col_b = st.columns([3,1])
    with col_a:
        wl_stock = st.text_input
