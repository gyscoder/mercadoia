import sqlite3
from datetime import datetime, timedelta
import statistics

def get_market_data(symbol='BTCUSDT', interval='1h', limit=100):
    """Fetch market data from SQLite database"""
    conn = sqlite3.connect('market_data.db')
    cursor = conn.cursor()
    query = '''
    SELECT timestamp, open, high, low, close, volume
    FROM market_data
    WHERE symbol = ? AND interval = ?
    ORDER BY timestamp DESC
    LIMIT ?
    '''
    cursor.execute(query, (symbol, interval, limit))
    rows = cursor.fetchall()
    conn.close()

    # Convert to list of dicts and reverse to get chronological order
    data = []
    for row in reversed(rows):  # Reverse to get oldest first
        data.append({
            'timestamp': row[0],
            'open': float(row[1]),
            'high': float(row[2]),
            'low': float(row[3]),
            'close': float(row[4]),
            'volume': float(row[5])
        })
    return data

def calculate_sma(prices, window):
    """Calculate Simple Moving Average"""
    if len(prices) < window:
        return None
    return sum(prices[-window:]) / window

def calculate_ema(prices, window):
    """Calculate Exponential Moving Average"""
    if len(prices) < window:
        return None

    multiplier = 2 / (window + 1)
    ema = prices[0]  # Start with first price

    for price in prices[1:]:
        ema = (price - ema) * multiplier + ema

    return ema

def calculate_rsi(prices, window=14):
    """Calculate Relative Strength Index"""
    if len(prices) < window + 1:
        return None

    gains = []
    losses = []

    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    if len(gains) < window:
        return None

    avg_gain = sum(gains[-window:]) / window
    avg_loss = sum(losses[-window:]) / window

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def detect_patterns(symbol='BTCUSDT'):
    """Detect trading patterns in market data"""
    print(f"Analyzing {symbol} for patterns...")

    # Get data
    data = get_market_data(symbol=symbol, interval='1h', limit=100)
    if not data or len(data) < 50:
        print("Insufficient data for pattern detection")
        return

    close_prices = [d['close'] for d in data]
    high_prices = [d['high'] for d in data]
    low_prices = [d['low'] for d in data]
    volumes = [d['volume'] for d in data]

    # Calculate indicators for latest data point
    latest = data[-1]
    prev = data[-2] if len(data) > 1 else latest

    # Calculate SMAs
    sma_20 = calculate_sma(close_prices, 20)
    sma_50 = calculate_sma(close_prices, 50) if len(close_prices) >= 50 else None

    # Calculate EMAs
    ema_12 = calculate_ema(close_prices, 12)
    ema_26 = calculate_ema(close_prices, 26)

    # Calculate RSI
    rsi = calculate_rsi(close_prices)

    # Calculate MACD
    macd = ema_12 - ema_26 if ema_12 is not None and ema_26 is not None else None
    # For simplicity, we'll calculate signal line as EMA of MACD (would need MACD history)
    macd_signal = None  # Simplified

    print("\n=== LATEST MARKET DATA ===")
    print(f"Timestamp: {latest['timestamp']}")
    print(f"Price: ${latest['close']:,.2f}")
    print(f"Change: {((latest['close'] - prev['close']) / prev['close'] * 100):+.2f}%")
    print(f"Volume: {latest['volume']:,.2f}")

    print("\n=== TECHNICAL INDICATORS ===")
    if sma_20 is not None:
        print(f"SMA(20): ${sma_20:,.2f}")
    if sma_50 is not None:
        print(f"SMA(50): ${sma_50:,.2f}")
    if ema_12 is not None:
        print(f"EMA(12): ${ema_12:,.2f}")
    if ema_26 is not None:
        print(f"EMA(26): ${ema_26:,.2f}")
    if rsi is not None:
        print(f"RSI: {rsi:.2f}")
    if macd is not None:
        print(f"MACD: {macd:.4f}")

    # Pattern detection signals
    signals = []

    # Trend signals
    if sma_20 is not None and sma_50 is not None:
        if latest['close'] > sma_20 > sma_50:
            signals.append("📈 Strong Uptrend (Price > SMA20 > SMA50)")
        elif latest['close'] < sma_20 < sma_50:
            signals.append("📉 Strong Downtrend (Price < SMA20 < SMA50)")
        elif latest['close'] > sma_20:
            signals.append("📈 Mild Uptrend (Price > SMA20)")
        elif latest['close'] < sma_20:
            signals.append("📉 Mild Downtrend (Price < SMA20)")

    # RSI signals
    if rsi is not None:
        if rsi > 70:
            signals.append("⚠️ Overbought (RSI > 70)")
        elif rsi < 30:
            signals.append("⚠️ Oversold (RSI < 30)")
        elif rsi > 50:
            signals.append("📈 Bullish Momentum (RSI > 50)")
        else:
            signals.append("📉 Bearish Momentum (RSI < 50)")

    # Price action
    if len(data) >= 2:
        if latest['close'] > prev['close'] and latest['high'] > prev['high'] and latest['low'] > prev['low']:
            signals.append("📈 Strong Bullish Candle (Higher High, Higher Low)")
        elif latest['close'] < prev['close'] and latest['high'] < prev['high'] and latest['low'] < prev['low']:
            signals.append("📉 Strong Bearish Candle (Lower High, Lower Low)")
        elif latest['close'] > prev['close']:
            signals.append("📈 Upward Momentum (Higher Close)")
        elif latest['close'] < prev['close']:
            signals.append("📉 Downward Momentum (Lower Close)")

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

    return data

if __name__ == '__main__':
    detect_patterns('BTCUSDT')