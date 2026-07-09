import sqlite3
from datetime import datetime, timedelta

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

def send_console_alert(message, level="INFO"):
    """Send alert to console with timestamp and emoji"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if level == "ALERT":
        print(f"[{timestamp}] (a) ALERT: {message}")
    elif level == "WARNING":
        print(f"[{timestamp}]  (w) WARNING: {message}")
    elif level == "SUCCESS":
        print(f"[{timestamp}] (s) SUCCESS: {message}")
    else:
        print(f"[{timestamp}] (i)  INFO: {message}")

def check_alert_conditions(data):
    """Check for conditions that should trigger alerts"""
    alerts = []

    if not data or len(data) < 2:
        return alerts

    latest = data[-1]
    prev = data[-2] if len(data) > 1 else latest

    close_prices = [d['close'] for d in data]
    if len(close_prices) < 20:
        return alerts

    # Calculate indicators for alert checking
    sma_20 = calculate_sma(close_prices, 20)
    sma_50 = calculate_sma(close_prices, 50) if len(close_prices) >= 50 else None
    rsi = calculate_rsi(close_prices)

    # Alert conditions
    if rsi is not None:
        if rsi < 25:
            alerts.append(("RSI extremely oversold (<25) - Potential buying opportunity", "ALERT"))
        elif rsi > 75:
            alerts.append(("RSI extremely overbought (>75) - Consider taking profits", "ALERT"))
        elif rsi < 30:
            alerts.append(("RSI oversold (<30) - Monitor for bounce", "WARNING"))
        elif rsi > 70:
            alerts.append(("RSI overbought (>70) - Watch for pullback", "WARNING"))

    if sma_20 is not None and sma_50 is not None:
        # Golden Cross / Death Cross detection
        if len(close_prices) >= 51:
            prev_sma_20 = calculate_sma(close_prices[:-1], 20)
            prev_sma_50 = calculate_sma(close_prices[:-1], 50)
            if prev_sma_20 and prev_sma_50:
                if sma_20 > sma_50 and prev_sma_20 <= prev_sma_50:
                    alerts.append(("Golden Cross detected (SMA20 crossed above SMA50) - Bullish signal", "SUCCESS"))
                elif sma_20 < sma_50 and prev_sma_20 >= prev_sma_50:
                    alerts.append(("Death Cross detected (SMA20 crossed below SMA50) - Bearish signal", "ALERT"))

    # Significant price movement
    price_change_pct = ((latest['close'] - prev['close']) / prev['close']) * 100
    if abs(price_change_pct) > 3.0:  # More than 3% move
        direction = "up" if price_change_pct > 0 else "down"
        alerts.append((f"Significant price movement: {price_change_pct:+.2f}% {direction}", "WARNING"))

    # Volume spike
    if len(data) >= 20:
        recent_volumes = [d['volume'] for d in data[-20:]]
        avg_volume = sum(recent_volumes) / len(recent_volumes)
        if latest['volume'] > avg_volume * 2:  # Volume 2x average
            alerts.append((f"Volume spike detected: {((latest['volume']/avg_volume)-1)*100:+.0f}% above average", "WARNING"))

    return alerts

def detect_patterns_with_alerts(symbol='BTCUSDT'):
    """Detect trading patterns and generate alerts"""
    print(f"Analyzing {symbol} for patterns with alert system...")

    # Get data
    data = get_market_data(symbol=symbol, interval='1h', limit=100)
    if not data or len(data) < 50:
        print("Insufficient data for pattern detection")
        return None

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

    # Pattern detection signals (for display)
    signals = []

    # Trend signals
    if sma_20 is not None and sma_50 is not None:
        if latest['close'] > sma_20 > sma_50:
            signals.append("TREND_UP_STRONG: Price > SMA20 > SMA50")
        elif latest['close'] < sma_20 < sma_50:
            signals.append("TREND_DOWN_STRONG: Price < SMA20 < SMA50")
        elif latest['close'] > sma_20:
            signals.append("TREND_UP_MILD: Price > SMA20")
        elif latest['close'] < sma_20:
            signals.append("TREND_DOWN_MILD: Price < SMA20")

    # RSI signals
    if rsi is not None:
        if rsi > 70:
            signals.append("RSI_OVERBOUGHT: RSI > 70")
        elif rsi < 30:
            signals.append("RSI_OVERSOLD: RSI < 30")
        elif rsi > 50:
            signals.append("RSI_BULLISH: RSI > 50")
        else:
            signals.append("RSI_BEARISH: RSI < 50")

    # Price action
    if len(data) >= 2:
        if latest['close'] > prev['close'] and latest['high'] > prev['high'] and latest['low'] > prev['low']:
            signals.append("PRICE_STRONG_BULL: Higher High, Higher Low")
        elif latest['close'] < prev['close'] and latest['high'] < prev['high'] and latest['low'] < prev['low']:
            signals.append("PRICE_STRONG_BEAR: Lower High, Lower Low")
        elif latest['close'] > prev['close']:
            signals.append("PRICE_UP: Higher Close")
        elif latest['close'] < prev['close']:
            signals.append("PRICE_DOWN: Lower Close")

    print("\n=== TRADING SIGNALS ===")
    for signal in signals:
        print(signal)

    # Overall assessment
    bullish_score = sum(1 for s in signals if 'TREND_UP' in s or 'RSI_BULLISH' in s or 'PRICE_UP' in s or 'PRICE_STRONG_BULL' in s)
    bearish_score = sum(1 for s in signals if 'TREND_DOWN' in s or 'RSI_BEARISH' in s or 'PRICE_DOWN' in s or 'PRICE_STRONG_BEAR' in s)

    print(f"\n=== OVERALL ASSESSMENT ===")
    if bullish_score > bearish_score:
        print(f"🟢 BULLISH ({bullish_score} bullish vs {bearish_score} bearish signals)")
    elif bearish_score > bullish_score:
        print(f"🔴 BEARISH ({bearish_score} bearish vs {bullish_score} bullish signals)")
    else:
        print(f"⚪ NEUTRAL ({bullish_score} bullish vs {bearish_score} bearish signals)")

    # Check for alerts
    print("\n=== ALERT CHECK ===")
    alerts = check_alert_conditions(data)
    if alerts:
        for msg, level in alerts:
            send_console_alert(f"{symbol}: {msg}", level)
    else:
        send_console_alert(f"{symbol}: No alert conditions met", "INFO")

    return {
        'data': data,
        'latest': latest,
        'indicators': {
            'sma_20': sma_20,
            'sma_50': sma_50,
            'ema_12': ema_12,
            'ema_26': ema_26,
            'rsi': rsi,
            'macd': macd
        },
        'signals': signals,
        'assessment': 'BULLISH' if bullish_score > bearish_score else 'BEARISH' if bearish_score > bullish_score else 'NEUTRAL',
        'alerts': alerts
    }

def calculate_bollinger_bands(prices, period=20, num_std_dev=2):
    """Calcula a Media Movel Central, Banda Superior e Banda Inferior"""
    if len(prices) < period:
        return None, None, None
    
    # Pega apenas o corte do período desejado
    sub_prices = prices[-period:]
    
    # Média Móvel Simples (Linha Central)
    sma = sum(sub_prices) / period
    
    # Cálculo do Desvio Padrão Populacional Nativo
    variance = sum((x - sma) ** 2 for x in sub_prices) / period
    std_dev = variance ** 0.5
    
    # Bandas Superior e Inferior
    upper_band = sma + (num_std_dev * std_dev)
    lower_band = sma - (num_std_dev * std_dev)
    
    return upper_band, sma, lower_band

if __name__ == '__main__':
    result = detect_patterns_with_alerts('BTCUSDT')