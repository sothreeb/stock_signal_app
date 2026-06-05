# Short-term Stock Signal Tracker

## Mac运行方法

1. 打开 Terminal
2. 进入文件夹：

```bash
cd stock_signal_app
```

3. 安装依赖：

```bash
pip3 install -r requirements.txt
```

4. 启动：

```bash
streamlit run app.py
```

## 说明

当前版本使用 Yahoo Finance 数据源做原型，适合先验证你的短线规则。
后续可以接 Longbridge OpenAPI，实现更接近你 Longbridge App 的实时行情、持仓和新闻。

默认股票池：LUNR, RKLB, ASTS, IREN, MRVL。

## 信号逻辑

- 买点1：突破 EMA5/10/20 上方
- 买点2：跌到 EMA30 / ATR 支撑附近观察
- 止损1：跌破短线支撑
- 硬止损：当前价 - 1ATR
- 止盈：+10%, +15%, +20%
- 评分：EMA、RSI、MACD、成交量综合评分

## 下一步 Longbridge 对接

需要你准备 Longbridge Developer 的：
- App Key
- App Secret
- Access Token

不要把这些密钥发给别人，也不要发到聊天里。放在你自己 Mac 的环境变量里即可。
