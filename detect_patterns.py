import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_market_data(symbol='BTCUSDT', interval='1h', limit=100):
    """Fetch market data from SQLite database"""
    conn = sqlite3.connect('market_data.db')
    query = '''
    SELECT timestamp, open, high, low, close, volume
    FROM market_data
    WHERE symbol = ? AND interval = ?
    ORDER BY timestamp
    '''
    df = pd.read_sql_query(query, conn, params=(symbol, interval))
    conn.close()

    if df.empty:
        return None

    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    return df

def calculate_sma(data, window):
    """Calculate Simple Moving Average"""
    return data.rolling(window=window).mean()

def calculate_ema(data, window):
    """Calculate Exponential Moving Average"""
    return data.ewm(span=window, adjust=False).mean()

def calculate_rsi(data, window=14):
    """Calculate Relative Strength Index"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def detect_patterns(symbol='BTCUSDT'):
    """Detect trading patterns in market data"""
    print(f"Analyzing {symbol} for patterns...")

    # Get data
    df = get_market_data(symbol=symbol, interval='1h')
    if df is None or len(df) < 50:
        print("Insufficient data for pattern detection")
        return

    close_prices = df['close']

    # Calculate indicators
    df['sma_20'] = calculate_sma(close_prices, 20)
    df['sma_50'] = calculate_sma(close_prices, 50)
    df['ema_12'] = calculate_ema(close_prices, 12)
    df['ema_26'] = calculate_ema(close_prices, 26)
    df['rsi'] = calculate_rsi(close_prices)

    # MACD
    df['macd'] = df['ema_12'] - df['ema_26']
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']

    # Get latest values
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    print("\n=== LATEST MARKET DATA ===")
    print(f"Timestamp: {latest.name}")
    print(f"Price: ${latest['close']:,.2f}")
    print(f"Change: {((latest['close'] - prev['close']) / prev['close'] * 100):+.2f}%")

    print("\n=== TECHNICAL INDICATORS ===")
    print(f"SMA(20): ${latest['sma_20']:,.2f}")
    print(f"SMA(50): ${latest['sma_50']:,.2f}")
    print(f"EMA(12): ${latest['ema_12']:,.2f}")
    print(f"EMA(26): ${latest['ema_26']:,.2f}")
    print(f"RSI: {latest['rsi']:.2f}")
    print(f"MACD: {latest['macd']:.4f}")
    print(f"MACD Signal: {latest['macd_signal']:.4f}")
    print(f"MACD Hist: {latest['macd_hist']:.4f}")

    # Pattern detection signals
    signals = []

    # Trend signals
    if latest['close'] > latest['sma_20'] > latest['sma_50']:
        signals.append("📈 Strong Uptrend (Price > SMA20 > SMA50)")
    elif latest['close'] < latest['sma_20'] < latest['sma_50']:
        signals.append("📉 Strong Downtrend (Price < SMA20 < SMA50)")
    elif latest['close'] > latest['sma_20']:
        signals.append("📈 Mild Uptrend (Price > SMA20)")
    elif latest['close'] < latest['sma_20']:
        signals.append("📉 Mild Downtrend (Price < SMA20)")

    # RSI signals
    if latest['rsi'] > 70:
        signals.append("⚠️ Overbought (RSI > 70)")
    elif latest['rsi'] < 30:
        signals.append("⚠️ Oversold (RSI < 30)")
    elif latest['rsi'] > 50:
        signals.append("📈 Bullish Momentum (RSI > 50)")
    else:
        signals.append("📉 Bearish Momentum (RSI < 50)")

    # MACD signals
    if latest['macd'] > latest['macd_signal'] and prev['macd'] <= prev['macd_signal']:
        signals.append("🚀 MACD Bullish Crossover")
    elif latest['macd'] < latest['macd_signal'] and prev['macd'] >= prev['macd_signal']:
        signals.append("💥 MACD Bearish Crossover")
    elif latest['macd'] > latest['macd_signal']:
        signals.append("📈 MACD Bullish")
    else:
        signals.append("📉 MACD Bearish")

    # Price action
    if latest['close'] > prev['close'] and latest['high'] > prev['high'] and latest['low'] > prev['low']:
        signals.append("📈 Strong Bullish Candle (Higher High, Higher Low)")
    elif latest['close'] < prev['close'] and latest['high'] < prev['high'] and latest['low'] < prev['low']:
        signals.append("📉 Strong Bearish Candle (Lower High, Lower Low)")

    print("\n=== TRADING SIGNALS ===")
    for signal in signals:
        print(signal)

    # Overall assessment
    bullish_score = sum(1 for s in signals if '📈' in s or '🚀' in s)
    bearish_score = sum(1 for s in signals if '📉' in s or '💥' in s)

    print(f"\n=== OVERALL ASSESSMENT ===")
    if bullish_score > bearish_score:
        print(f"🟢 BULLISH ({bullish_score} bullish vs {bearish_score} bearish signals)")
    elif bearish_score > bullish_score:
        print(f"🔴 BEARISH ({bearish_score} bearish vs {bullish_score} bullish signals)")
    else:
        print(f"⚪ NEUTRAL ({bullish_score} bullish vs {bearish_score} bearish signals)")

    return df

if __name__ == '__main__':
    detect_patterns('BTCUSDT')