import streamlit as st
import pandas as pd
import yfinance as yf
from github import Github
import json
import requests
from io import StringIO

# ---------------- CONFIG ----------------
GITHUB_TOKEN = "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"
REPO_NAME = "rdktech777/marketdashboard"  # your GitHub repo
PORTFOLIO_FILE = "portfolio.json"
WATCHLIST_FILE = "watchlist.json"

# GitHub helper functions
def load_from_github(file_name):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    try:
        content = repo.get_contents(file_name)
        return json.loads(content.decoded_content.decode())
    except:
        # If file doesn't exist, return empty
        return {}

def save_to_github(file_name, data, commit_message):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    content = None
    try:
        content = repo.get_contents(file_name)
        repo.update_file(file_name, commit_message, json.dumps(data, indent=2), content.sha)
    except:
        repo.create_file(file_name, commit_message, json.dumps(data, indent=2))

# ---------------- LOAD DATA ----------------
portfolio = load_from_github(PORTFOLIO_FILE)
watchlist = load_from_github(WATCHLIST_FILE)

# ---------------- UTILS ----------------
def get_live_data(symbols):
    live_data = []
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            live_data.append({
                "Symbol": symbol,
                "LTP": info.get("regularMarketPrice"),
                "Change": info.get("regularMarketChangePercent"),
                "Previous Close": info.get("previousClose"),
            })
        except:
            live_data.append({
                "Symbol": symbol,
                "LTP": None,
                "Change": None,
                "Previous Close": None,
            })
    return pd.DataFrame(live_data)

def display_table(data_dict):
    if data_dict:
        df = pd.DataFrame.from_dict(data_dict, orient='index')
        st.dataframe(df)
    else:
        st.info("No data available.")

# ---------------- STREAMLIT UI ----------------
st.set_page_config(page_title="📈 Professional Stock Dashboard", layout="wide")
st.title("📈 Professional Stock Portfolio Dashboard")

# Tabs
tab1, tab2 = st.tabs(["Portfolio", "Watchlist"])

# ---------------- PORTFOLIO TAB ----------------
with tab1:
    st.header("💼 Portfolio")
    display_table(portfolio)
    
    with st.expander("➕ Add/Update Stock in Portfolio"):
        symbol = st.text_input("Stock Symbol (e.g., TCS.NS)")
        qty = st.number_input("Quantity", min_value=1, step=1)
        avg_price = st.number_input("Average Price", min_value=0.0, format="%.2f")
        if st.button("Add / Update Portfolio"):
            portfolio[symbol] = {"Qty": qty, "Avg Price": avg_price}
            save_to_github(PORTFOLIO_FILE, portfolio, f"Update portfolio: {symbol}")
            st.success(f"{symbol} added/updated in portfolio!")

    st.subheader("📊 Live Portfolio Data")
    if portfolio:
        symbols = list(portfolio.keys())
        live_df = get_live_data(symbols)
        live_df["Qty"] = live_df["Symbol"].map(lambda x: portfolio[x]["Qty"])
        live_df["Avg Price"] = live_df["Symbol"].map(lambda x: portfolio[x]["Avg Price"])
        live_df["Investment Value"] = live_df["Qty"] * live_df["Avg Price"]
        live_df["Current Value"] = live_df["Qty"] * live_df["LTP"]
        live_df["P/L"] = live_df["Current Value"] - live_df["Investment Value"]
        st.dataframe(live_df)

# ---------------- WATCHLIST TAB ----------------
with tab2:
    st.header("🔖 Watchlist")
    display_table(watchlist)

    with st.expander("➕ Add Stock to Watchlist"):
        wsymbol = st.text_input("Watchlist Symbol (e.g., INFY.NS)")
        if st.button("Add to Watchlist"):
            watchlist[wsymbol] = {}
            save_to_github(WATCHLIST_FILE, watchlist, f"Add {wsymbol} to watchlist")
            st.success(f"{wsymbol} added to watchlist!")

    st.subheader("📈 Live Watchlist Data")
    if watchlist:
        wsymbols = list(watchlist.keys())
        watch_df = get_live_data(wsymbols)
        st.dataframe(watch_df)
