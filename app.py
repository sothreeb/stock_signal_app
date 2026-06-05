import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Stock Signal Tracker", layout="wide")

TICKERS = ["LUNR", "RKLB", "ASTS", "IREN", "MRVL"]

def rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def analyze(ticker):
    df = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=False)
    if df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]

    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    price = float(close.iloc[-1])
    ema5 = float(close.ewm(span=5, adjust=False).mean().iloc[-1])
    ema10 = float(close.ewm(span=10, adjust=False).mean().iloc[-1])
    ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
    ema30 = float(close.ewm(span=30, adjust=False).mean().iloc[-1])
    rsi14 = float(rsi(close).iloc[-1])

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)

    atr = float(tr.rolling(14).mean().iloc[-1])

    score = 50
    if price > ema5:
        score += 15
    if price > ema20:
        score += 15
    if rsi14 > 50:
        score += 10
    if rsi14 > 80:
        score -= 20
    if price < ema10:
        score -= 15

    score = max(0, min(100, score))

    if score >= 75:
        action = "可以买，但分批"
    elif score >= 60:
        action = "观察，等确认"
    elif rsi14 < 30:
        action = "超跌，等止跌K线"
    else:
        action = "等待"

    return {
        "Ticker": ticker,
        "Price": round(price, 2),
        "Score": score,
        "Action": action,
        "EMA5": round(ema5, 2),
        "EMA10": round(ema10, 2),
        "EMA20": round(ema20, 2),
        "EMA30": round(ema30, 2),
        "RSI14": round(rsi14, 2),
        "ATR": round(atr, 2),
        "突破买点": round(ema5 * 1.01, 2),
        "回调观察": round(price - atr * 0.5, 2),
        "止损": round(price - atr, 2),
        "硬止损": round(price - atr * 1.5, 2),
        "止盈10%": round(price * 1.10, 2),
        "止盈15%": round(price * 1.15, 2),
        "止盈20%": round(price * 1.20, 2),
    }

st.title("📈 Short-term Stock Signal Tracker")
st.caption("数据源：Yahoo Finance。仅用于短线观察，不是投资建议。")

rows = []
for ticker in TICKERS:
    result = analyze(ticker)
    if result:
        rows.append(result)

df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True)

st.subheader("操作规则")
st.write("""
- Score ≥ 75：趋势较强，可以考虑分批。
- Score 60～74：观察，等突破确认。
- RSI > 80：不要追高，考虑止盈。
- RSI < 30：超跌，但要等十字星或阳线确认。
- 跌破止损：短线必须认错，不要死扛。
""")