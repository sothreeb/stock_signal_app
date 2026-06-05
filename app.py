import math
from datetime import datetime
import pandas as pd
import numpy as np
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Short-term Stock Signal Tracker", layout="wide")

DEFAULT_TICKERS = ["LUNR", "RKLB", "ASTS", "IREN", "MRVL"]


def ema(s, span):
    return s.ewm(span=span, adjust=False).mean()


def rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def atr(df, period=14):
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def macd(close):
    dif = ema(close, 12) - ema(close, 26)
    dea = ema(dif, 9)
    hist = dif - dea
    return dif, dea, hist


def analyze(symbol: str):
    df = yf.download(symbol, period="6mo", interval="1d", auto_adjust=False, progress=False)
    if df.empty:
        return None, None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    df = df.dropna().copy()
    df["EMA5"] = ema(df["Close"], 5)
    df["EMA10"] = ema(df["Close"], 10)
    df["EMA20"] = ema(df["Close"], 20)
    df["EMA30"] = ema(df["Close"], 30)
    df["RSI14"] = rsi(df["Close"], 14)
    df["ATR14"] = atr(df, 14)
    df["DIF"], df["DEA"], df["MACD"] = macd(df["Close"])
    df["VolMA5"] = df["Volume"].rolling(5).mean()
    last = df.iloc[-1]
    prev = df.iloc[-2]
    price = float(last["Close"])
    ema5, ema10, ema20, ema30 = [float(last[x]) for x in ["EMA5", "EMA10", "EMA20", "EMA30"]]
    rsi14 = float(last["RSI14"]) if not math.isnan(last["RSI14"]) else None
    atr14 = float(last["ATR14"]) if not math.isnan(last["ATR14"]) else None
    vol_ratio = float(last["Volume"] / last["VolMA5"]) if last["VolMA5"] else 0
    macd_state = "金叉/偏强" if last["DIF"] > last["DEA"] else "死叉/偏弱"

    score = 50
    reasons = []
    if price > ema5: score += 12; reasons.append("站上EMA5")
    else: score -= 12; reasons.append("跌破EMA5")
    if price > ema20: score += 10; reasons.append("站上EMA20")
    else: score -= 10; reasons.append("跌破EMA20")
    if ema5 > ema10 > ema20: score += 12; reasons.append("短均线多头排列")
    if rsi14 is not None:
        if rsi14 < 30: score += 8; reasons.append("RSI超跌，可能有反弹")
        elif rsi14 > 80: score -= 18; reasons.append("RSI超买，追高危险")
        elif 45 <= rsi14 <= 65: score += 6; reasons.append("RSI处于健康区间")
    if vol_ratio > 1.5 and price > prev["Close"]: score += 10; reasons.append("放量上涨")
    if last["DIF"] > last["DEA"]: score += 8
    else: score -= 8
    score = max(0, min(100, int(score)))

    breakout_buy = round(max(ema5, ema10, ema20) * 1.01, 2)
    dip_buy = round(max(ema30, price - (atr14 or price*0.08)*0.5), 2)
    hard_stop = round(price - (atr14 or price*0.08), 2)
    support_stop = round(min(ema30, price * 0.94), 2)
    tp1, tp2, tp3 = [round(price * x, 2) for x in [1.10, 1.15, 1.20]]

    if score >= 75:
        action = "可考虑分批买入/加关注"
    elif score >= 60:
        action = "观察，等确认信号"
    elif score >= 40:
        action = "暂不追，等站回EMA或超跌"
    else:
        action = "弱势，优先回避"

    result = {
        "Ticker": symbol, "Price": round(price, 2), "Score": score, "Action": action,
        "Breakout Buy": breakout_buy, "Dip Watch": dip_buy, "Stop 1": support_stop,
        "Hard Stop": hard_stop, "TP +10%": tp1, "TP +15%": tp2, "TP +20%": tp3,
        "EMA5": round(ema5,2), "EMA10": round(ema10,2), "EMA20": round(ema20,2), "EMA30": round(ema30,2),
        "RSI14": round(rsi14,1) if rsi14 is not None else None, "ATR14": round(atr14,2) if atr14 is not None else None,
        "Volume/MA5": round(vol_ratio,2), "MACD": macd_state, "Reasons": " / ".join(reasons)
    }
    return result, df

st.title("📈 短线股票追踪分析 App")
st.caption("EMA + RSI + MACD + ATR 规则评分。只做提醒和分析，不自动下单。")

tickers = st.text_input("股票池，用逗号分隔", ",".join(DEFAULT_TICKERS)).upper().replace(" ", "").split(",")
run = st.button("刷新分析")

if run or True:
    rows = []
    charts = {}
    for t in tickers:
        if not t: continue
        res, df = analyze(t)
        if res:
            rows.append(res)
            charts[t] = df
    if rows:
        out = pd.DataFrame(rows).sort_values("Score", ascending=False)
        st.dataframe(out[["Ticker","Price","Score","Action","Breakout Buy","Dip Watch","Stop 1","Hard Stop","TP +10%","TP +15%","TP +20%","RSI14","MACD","Reasons"]], use_container_width=True)
        selected = st.selectbox("查看K线指标", out["Ticker"].tolist())
        df = charts[selected]
        st.line_chart(df[["Close","EMA5","EMA10","EMA20","EMA30"]].tail(90))
        st.line_chart(df[["RSI14"]].tail(90))

st.warning("这不是投资建议。高波动股票容易盘前/盘后大幅跳空，止损价不一定能成交。")
