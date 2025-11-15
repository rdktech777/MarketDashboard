import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Indian Stock Dashboard", layout="wide")

st.title("📈 Indian Stock Portfolio Dashboard")

# ---- Portfolio Table ----
st.subheader("Your Portfolio")

if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=["Stock", "Qty", "Avg Price"])

# Add new stock
with st.expander("➕ Add New Stock"):
    s = st.text_input("Stock Symbol (NSE) e.g. TCS.NS")
    q = st.number_input("Quantity", step=1)
    p = st.number_input("Average Price", step=1.0)
    if st.button("Add"):
        st.session_state.portfolio.loc[len(st.session_state.portfolio)] = [s, q, p]
        st.success("Added!")

# delete option
if len(st.session_state.portfolio) > 0:
    delete_index = st.selectbox("Delete a stock", [None] + list(st.session_state.portfolio.index))
    if st.button("Delete Stock") and delete_index is not None:
        st.session_state.portfolio.drop(delete_index, inplace=True)
        st.success("Deleted!")

st.write(st.session_state.portfolio)

# ---- Market Price Fetch ----
if len(st.session_state.portfolio) > 0:
    st.subheader("Live Prices (or LTP when market is closed)")

    data = []
    for idx, row in st.session_state.portfolio.iterrows():
        try:
            ticker = yf.Ticker(row["Stock"])
            price = ticker.history(period="1d")["Close"].iloc[-1]   # LTP
            value = price * row["Qty"]
            gain = (price - row["Avg Price"]) * row["Qty"]

            data.append([row["Stock"], price, value, gain])

        except:
            data.append([row["Stock"], "Error", "Error", "Error"])

    df2 = pd.DataFrame(data, columns=["Stock", "LTP", "Current Value", "Gain/Loss"])
    st.dataframe(df2)

