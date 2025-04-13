import ccxt
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ตรวจสอบว่า pandas_ta ถูกติดตั้ง
try:
    import pandas_ta as ta
except ImportError:
    st.error("ไม่พบโมดูล pandas_ta กรุณาติดตั้งด้วย: pip install pandas_ta")
    st.stop()

# สร้าง UI ด้วย Streamlit
st.title("Trading Analysis Dashboard - Binance TH")

# ฟังก์ชันให้ผู้ใช้กรอก API Key และ Secret Key
st.subheader("กรุณากรอกข้อมูล API (Binance TH)")
api_key = st.text_input("API Key", type="password")
api_secret = st.text_input("Secret Key", type="password")

# ตรวจสอบว่าผู้ใช้กรอก API Key และ Secret Key หรือไม่
if api_key and api_secret:
    try:
        # ล้างช่องว่างใน API Key และ Secret Key
        api_key = api_key.strip()
        api_secret = api_secret.strip()

        # เชื่อมต่อกับ Binance TH API
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,  # จำกัดอัตราการเรียก API
            'urls': {
                'api': {
                    'public': 'https://api.binance.th/api/v3',  # Market Data endpoint
                    'private': 'https://api.binance.th/api/v3'  # Private endpoint
                }
            },
            'options': {
                'adjustForTimeDifference': True,
                'defaultType': 'spot'  # ใช้ Spot trading
            }
        })

        # ทดสอบการเชื่อมต่อด้วยการดึง ticker
        exchange.fetch_ticker('BTC/USDT')
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อ API: {str(e)}")
        st.stop()

    def fetch_and_calculate(symbol, timeframe):
        try:
            # ดึงข้อมูล OHLCV จาก Binance TH
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # คำนวณ RSI
            df['RSI'] = ta.rsi(df['close'], length=14)
            
            # คำนวณ MACD
            macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
            df['MACD'] = macd['MACD_12_26_9']
            df['MACD_signal'] = macd['MACDS_12_26_9']
            df['MACD_hist'] = macd['MACDH_12_26_9']
            
            # คำนวณ SMA 50
            df['SMA50'] = ta.sma(df['close'], length=50)
            
            return df
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}")
            return None

    # เลือกสัญลักษณ์
    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT', 'LTC/USDT']
    symbol = st.selectbox("เลือกสัญลักษณ์", symbols)

    # เลือกช่วงเวลา
    timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
    timeframe = st.selectbox("เลือกช่วงเวลา", timeframes)

    # ดึงข้อมูลและคำนวณ
    df = fetch_and_calculate(symbol, timeframe)
    
    if df is not None:
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
