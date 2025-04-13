import ccxt
import pandas as pd
import talib
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# สร้าง UI ด้วย Streamlit
st.title("Trading Analysis Dashboard")

# ฟังก์ชันให้ผู้ใช้กรอก API Key และ Secret Key
st.subheader("กรุณากรอกข้อมูล API")
api_key = st.text_input("API Key", type="password")
api_secret = st.text_input("Secret Key", type="password")

# ตรวจสอบว่าผู้ใช้กรอก API Key และ Secret Key หรือไม่
if api_key and api_secret:
    # เชื่อมต่อกับ Binance โดยใช้ API Key และ Secret Key ที่ผู้ใช้กรอก
    exchange = ccxt.binance({
        'apiKey': api_key,
        'secret': api_secret,
        'options': {'adjustForTimeDifference': True},
    })

    # ฟังก์ชันดึงข้อมูลและคำนวณอินดิเคเตอร์
    def fetch_and_calculate(symbol, timeframe):
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # คำนวณ RSI
        df['RSI'] = talib.RSI(df['close'], timeperiod=14)
        
        # คำนวณ MACD
        macd, signal, hist = talib.MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
        df['MACD'] = macd
        df['MACD_signal'] = signal
        df['MACD_hist'] = hist
        
        # คำนวณ SMA 50
        df['SMA50'] = talib.SMA(df['close'], timeperiod=50)
        
        return df

    # เลือกสัญลักษณ์
    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT', 'LTC/USDT']
    symbol = st.selectbox("เลือกสัญลักษณ์", symbols)

    # เลือกช่วงเวลา
    timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
    timeframe = st.selectbox("เลือกช่วงเวลา", timeframes)

    # ดึงข้อมูลและคำนวณ
    df = fetch_and_calculate(symbol, timeframe)

    # แสดงข้อมูลล่าสุด
    st.subheader("ข้อมูลล่าสุด")
    st.write(df.tail(1))

    # สร้างกราฟ
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.1, subplot_titles=('Candlestick', 'RSI', 'MACD'),
                        row_heights=[0.5, 0.2, 0.3])

    # กราฟแท่งเทียน
    fig.add_trace(go.Candlestick(x=df['timestamp'],
                                 open=df['open'], high=df['high'],
                                 low=df['low'], close=df['close'],
                                 increasing_line_color='green', decreasing_line_color='red'),
                  row=1, col=1)

    # เพิ่มเส้น SMA50
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['SMA50'], name='SMA50', line=dict(color='orange')),
                  row=1, col=1)

    # กราฟ RSI
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['RSI'], name='RSI', line=dict(color='blue')),
                  row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    # กราฟ MACD
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['MACD'], name='MACD', line=dict(color='blue')),
                  row=3, col=1)
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['MACD_signal'], name='Signal', line=dict(color='orange')),
                  row=3, col=1)
    fig.add_trace(go.Bar(x=df['timestamp'], y=df['MACD_hist'], name='Histogram', marker_color='gray'),
                  row=3, col=1)

    # อัปเดต layout
    fig.update_layout(height=800, showlegend=False)

    # แสดงกราฟใน Streamlit
    st.plotly_chart(fig)
else:
    st.warning("กรุณากรอก API Key และ Secret Key เพื่อดำเนินการต่อ")