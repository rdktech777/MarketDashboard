import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
from github import Github

# ---------------- GitHub Setup ----------------
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO_NAME = "username/marketdashboard"  # Replace with your GitHub repo
BRANCH = "main"

def push_to_github(file_path, data_dict):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    content = json.dumps(data_dict, indent=4)
    try:
        contents = repo.get_contents(file_path, ref=BRANCH)
        repo.update_file(contents.path, f"Update {file_path}", content, contents.sha, branch=BRANCH)
    except:
        repo.create_file(file_path, f"Create {file_path}", content, branch=BRANCH)

def load_from_github(file_path):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    try:
        contents = repo.get_contents(file_path, ref=BRANCH)
        return json.loads(contents.decoded_content.decode())
    except:
        return {}

# ---------------- Load Data ----------------
portfolio = load_from_github("portfolio.json")
watchlist = load_from_github("watchlist.json")

# ---------------- Streamlit UI ----------------
st.title("📈 Indian Stock Dashboard")

tab = st.tabs(["Portfolio", "Watchlist"])

# ---- Portfolio Tab ----
with tab[0]:
    st.subheader("Your Portfolio")
    st.write(portfolio)
    
    with st.expander("➕ Add / Update Stock"):
        stock = st.text_input("Stock Symbol (e.g. TCS.NS)").upper()
        qty = st.number_input("Quantity", min_value=1, step=1)
        avg_price = st.number_input("Average Price", min_value=0.0, step=0.01)
        if st.button("Add / Update"):
            portfolio[stock] = {"qty": qty, "avg_price": avg_price}
            push_to_github("portfolio.json", portfolio)
            st.success(f"{stock} saved!")

# ---- Watchlist Tab ----
with tab[1]:
    st.subheader("Your Watchlist")
    st.write(watchlist)
    
    with st.expander("➕ Add Stock to Watchlist"):
        stock = st.text_input("Stock Symbol (Watchlist)").upper()
        if st.button("Add to Watchlist"):
            watchlist[stock] = {}
            push_to_github("watchlist.json", watchlist)
            st.success(f"{stock} added to watchlist!")

# ---- Live Prices ----
st.subheader("Live Prices")
all_stocks = list(portfolio.keys()) + list(watchlist.keys())
if all_stocks:
    data = yf.download(all_stocks, period="1d", interval="1m")['Adj Close'].iloc[-1]
    st.table(data)
