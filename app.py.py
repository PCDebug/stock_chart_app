import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf

# Page config
st.set_page_config(page_title="Stock Chart Analyzer", layout="wide")
st.title("📈 Stock Candlestick Chart Analyzer")

# ===== HELPER FUNCTIONS =====

def calculate_sma(data, window=20):
    """Calculate Simple Moving Average"""
    return data['Close'].rolling(window=window).mean()

def calculate_ema(data, window=20):
    """Calculate Exponential Moving Average"""
    return data['Close'].ewm(span=window, adjust=False).mean()

def calculate_rsi(data, window=14):
    """Calculate Relative Strength Index"""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data, fast=12, slow=26, signal=9):
    """Calculate MACD"""
    ema_fast = data['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = data['Close'].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(data, window=20, num_std=2):
    """Calculate Bollinger Bands"""
    sma = data['Close'].rolling(window=window).mean()
    std = data['Close'].rolling(window=window).std()
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    return upper_band, sma, lower_band

@st.cache_data
def get_stock_data(ticker, period='1y'):
    """Download real stock data from yfinance"""
    try:
        data = yf.download(ticker, period=period, progress=False)
        data = data.reset_index()
        return data
    except Exception as e:
        st.error(f"Could not fetch data for {ticker}. Error: {e}")
        return None

# ===== SIDEBAR CONTROLS =====

st.sidebar.header("⚙️ Settings")

# Stock ticker input
ticker = st.sidebar.text_input("📊 Stock Ticker", value="AAPL").upper()
period = st.sidebar.selectbox("Time Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)

# Get data
df = get_stock_data(ticker, period)

if df is None:
    st.stop()

# Date range selector
st.sidebar.subheader("Date Range")
min_date = df['Date'].min()
max_date = df['Date'].max()
date_range = st.sidebar.slider(
    "Select date range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY-MM-DD"
)
df_filtered = df[(df['Date'] >= date_range[0]) & (df['Date'] <= date_range[1])].copy()

# Technical Indicators
st.sidebar.subheader("Technical Indicators")
show_sma = st.sidebar.checkbox("SMA (Simple Moving Average)", value=True)
sma_period = st.sidebar.slider("SMA Period", 5, 100, 20) if show_sma else 20

show_ema = st.sidebar.checkbox("EMA (Exponential Moving Average)", value=False)
ema_period = st.sidebar.slider("EMA Period", 5, 100, 12) if show_ema else 12

show_bb = st.sidebar.checkbox("Bollinger Bands", value=True)
bb_period = st.sidebar.slider("BB Period", 5, 50, 20) if show_bb else 20
bb_std = st.sidebar.slider("BB Std Dev", 1.0, 4.0, 2.0) if show_bb else 2.0

show_rsi = st.sidebar.checkbox("RSI (Relative Strength Index)", value=True)
rsi_period = st.sidebar.slider("RSI Period", 5, 30, 14) if show_rsi else 14

show_macd = st.sidebar.checkbox("MACD", value=True)

# ===== CALCULATE INDICATORS =====

if show_sma:
    df_filtered['SMA'] = calculate_sma(df_filtered, sma_period)

if show_ema:
    df_filtered['EMA'] = calculate_ema(df_filtered, ema_period)

if show_bb:
    df_filtered['BB_Upper'], df_filtered['BB_Middle'], df_filtered['BB_Lower'] = \
        calculate_bollinger_bands(df_filtered, bb_period, bb_std)

if show_rsi:
    df_filtered['RSI'] = calculate_rsi(df_filtered, rsi_period)

if show_macd:
    df_filtered['MACD'], df_filtered['MACD_Signal'], df_filtered['MACD_Hist'] = \
        calculate_macd(df_filtered)

# ===== MAIN CANDLESTICK CHART =====

st.subheader(f"Candlestick Chart - {ticker}")

fig = go.Figure()

# Add candlesticks
fig.add_trace(go.Candlestick(
    x=df_filtered['Date'],
    open=df_filtered['Open'],
    high=df_filtered['High'],
    low=df_filtered['Low'],
    close=df_filtered['Close'],
    name='Candlesticks',
    increasing_line_color='green',
    decreasing_line_color='red'
))

# Add SMA
if show_sma:
    fig.add_trace(go.Scatter(
        x=df_filtered['Date'],
        y=df_filtered['SMA'],
        mode='lines',
        name=f'SMA({sma_period})',
        line=dict(color='blue', width=2)
    ))

# Add EMA
if show_ema:
    fig.add_trace(go.Scatter(
        x=df_filtered['Date'],
        y=df_filtered['EMA'],
        mode='lines',
        name=f'EMA({ema_period})',
        line=dict(color='orange', width=2)
    ))

# Add Bollinger Bands
if show_bb:
    fig.add_trace(go.Scatter(
        x=df_filtered['Date'],
        y=df_filtered['BB_Upper'],
        mode='lines',
        name='BB Upper',
        line=dict(color='rgba(255,0,0,0)', width=0),
        showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=df_filtered['Date'],
        y=df_filtered['BB_Lower'],
        fill='tonexty',
        mode='lines',
        name='Bollinger Bands',
        line=dict(color='rgba(255,0,0,0)', width=0),
        fillcolor='rgba(0,100,200,0.1)'
    ))
    fig.add_trace(go.Scatter(
        x=df_filtered['Date'],
        y=df_filtered['BB_Middle'],
        mode='lines',
        name='BB Middle',
        line=dict(color='gray', width=1, dash='dash')
    ))

fig.update_layout(
    title=f"{ticker} - Stock Price with Technical Indicators",
    yaxis_title="Stock Price (USD)",
    xaxis_title="Date",
    template="plotly_dark",
    hovermode='x unified',
    height=500
)
st.plotly_chart(fig, use_container_width=True)

# ===== RSI CHART =====

if show_rsi:
    st.subheader("RSI (Relative Strength Index)")
    fig_rsi = go.Figure()
    
    fig_rsi.add_trace(go.Scatter(
        x=df_filtered['Date'],
        y=df_filtered['RSI'],
        mode='lines',
        name='RSI',
        line=dict(color='purple', width=2)
    ))
    
    # Add overbought/oversold lines
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought (70)")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold (30)")
    
    fig_rsi.update_layout(
        yaxis_title="RSI",
        xaxis_title="Date",
        template="plotly_dark",
        hovermode='x unified',
        height=300,
        yaxis=dict(range=[0, 100])
    )
    st.plotly_chart(fig_rsi, use_container_width=True)

# ===== MACD CHART =====

if show_macd:
    st.subheader("MACD (Moving Average Convergence Divergence)")
    fig_macd = go.Figure()
    
    fig_macd.add_trace(go.Scatter(
        x=df_filtered['Date'],
        y=df_filtered['MACD'],
        mode='lines',
        name='MACD',
        line=dict(color='blue', width=2)
    ))
    
    fig_macd.add_trace(go.Scatter(
        x=df_filtered['Date'],
        y=df_filtered['MACD_Signal'],
        mode='lines',
        name='Signal Line',
        line=dict(color='red', width=2)
    ))
    
    # Histogram as bar chart
    colors = ['green' if x > 0 else 'red' for x in df_filtered['MACD_Hist']]
    fig_macd.add_trace(go.Bar(
        x=df_filtered['Date'],
        y=df_filtered['MACD_Hist'],
        name='Histogram',
        marker_color=colors,
        opacity=0.3
    ))
    
    fig_macd.update_layout(
        yaxis_title="MACD Value",
        xaxis_title="Date",
        template="plotly_dark",
        hovermode='x unified',
        height=300
    )
    st.plotly_chart(fig_macd, use_container_width=True)

# ===== DATA TABLE =====

st.subheader("Recent Data")
columns_to_show = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
if show_sma:
    columns_to_show.append('SMA')
if show_ema:
    columns_to_show.append('EMA')
if show_rsi:
    columns_to_show.append('RSI')

display_df = df_filtered[columns_to_show].tail(20).copy()
display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
st.dataframe(display_df, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **How to use these indicators:**\n\n"
    "• **SMA/EMA**: Identify trends\n"
    "• **Bollinger Bands**: Volatility\n"
    "• **RSI**: Overbought (>70) / Oversold (<30)\n"
    "• **MACD**: Momentum & crossovers"
)
