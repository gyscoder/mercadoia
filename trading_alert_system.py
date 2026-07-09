import sqlite3
from datetime import datetime
import json
import os

class TradingAlertSystem:
    def __init__(self, db_path='market_data.db', alert_log='trading_alerts.log'):
        self.db_path = db_path
        self.alert_log = alert_log
        self.alert_history = self.load_alert_history()

    def log_alert(self, message, level="INFO"):
        """Log alert to console and file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Console output with emojis
        if level == "ALERT":
            print(f"[{timestamp}] 🚨 ALERT: {message}")
        elif level == "WARNING":
            print(f"[{timestamp}] ⚠️  WARNING: {message}")
        elif level == "SUCCESS":
            print(f"[{timestamp}] ✅ SUCCESS: {message}")
        else:
            print(f"[{timestamp}] ℹ️  INFO: {message}")

        # File logging
        try:
            with open(self.alert_log, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [{level}] {message}\n")
        except Exception as e:
            print(f"Error writing to alert log: {e}")

        # Add to history
        self.alert_history.append({
            "timestamp": timestamp,
            "level": level,
            "message": message
        })

        # Keep only last 100 alerts in memory
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]

    def save_alert_history(self):
        """Save alert history to JSON file"""
        try:
            with open("alert_history.json", "w", encoding="utf-8") as f:
                json.dump(self.alert_history, f, indent=2)
        except Exception as e:
            print(f"Error saving alert history: {e}")

    def load_alert_history(self):
        """Load alert history from JSON file"""
        try:
            if os.path.exists("alert_history.json"):
                with open("alert_history.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading alert history: {e}")
        return []

def get_latest_market_data(symbol='BTCUSDT', interval='1h', limit=100):
    """Get latest market data from database"""
    conn = None
    try:
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

        # Convert to list of dicts (oldest first)
        data = []
        for row in reversed(rows):
            data.append({
                'timestamp': row[0],
                'open': float(row[1]),
                'high': float(row[2]),
                'low': float(row[3]),
                'close': float(row[4]),
                'volume': float(row[5])
            })
        return data
    except Exception as e:
        print(f"Error getting market data: {e}")
        return []
    finally:
        if conn:
            conn.close()

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

def analyze_and_alert(symbol='BTCUSDT'):
    """Main function to analyze market data and generate alerts"""
    alert_system = TradingAlertSystem()

    print(f"🔍 Analyzing {symbol} for trading alerts...")
    print("=" * 50)

    # Get market data
    data = get_latest_market_data(symbol=symbol, interval='1h', limit=100)

    if not data or len(data) < 20:
        alert_system.log_alert(f"Insufficient data for {symbol} analysis", "WARNING")
        return

    latest = data[-1]
    prev = data[-2] if len(data) > 1 else latest

    # Extract price data
    close_prices = [d['close'] for d in data]

    # Calculate indicators
    sma_20 = calculate_sma(close_prices, 20)
    sma_50 = calculate_sma(close_prices, 50) if len(close_prices) >= 50 else None
    rsi = calculate_rsi(close_prices)

    # Display current status
    print(f"📊 {symbol} Analysis")
    print(f"   Time: {latest['timestamp']}")
    print(f"   Price: ${latest['close']:,.2f}")
    print(f"   Change: {((latest['close'] - prev['close']) / prev['close'] * 100):+.2f}%")
    print(f"   Volume: {latest['volume']:,.2f}")
    print()

    print(f"📈 Technical Indicators")
    if sma_20:
        print(f"   SMA(20): ${sma_20:,.2f}")
    if sma_50:
        print(f"   SMA(50): ${sma_50:,.2f}")
    if rsi is not None:
        print(f"   RSI(14): {rsi:.2f}")
    print()

    # Check for alert conditions
    alerts_triggered = []

    # RSI Alerts
    if rsi is not None:
        if rsi < 25:
            alerts_triggered.append(("RSI extremely oversold (<25) - Strong buying signal", "ALERT"))
        elif rsi < 30:
            alerts_triggered.append(("RSI oversold (<30) - Potential bounce opportunity", "WARNING"))
        elif rsi > 75:
            alerts_triggered.append(("RSI extremely overbought (>75) - Strong selling signal", "ALERT"))
        elif rsi > 70:
            alerts_triggered.append(("RSI overbought (>70) - Consider taking profits", "WARNING"))

    # Trend Alerts
    if sma_20 is not None and sma_50 is not None:
        price = latest['close']
        if price < sma_20 < sma_50:
            alerts_triggered.append(("Strong downtrend: Price < SMA20 < SMA50", "WARNING"))
        elif price > sma_20 > sma_50:
            alerts_triggered.append(("Strong uptrend: Price > SMA20 > SMA50", "SUCCESS"))
        elif sma_20 > sma_50 and price > sma_20:
            alerts_triggered.append(("Price above both SMAs with bullish alignment", "SUCCESS"))
        elif sma_20 < sma_50 and price < sma_20:
            alerts_triggered.append(("Price below both SMAs with bearish alignment", "WARNING"))

    # Price Action Alerts
    if len(data) >= 2:
        # Check for strong candles
        if (latest['close'] > prev['close'] and
            latest['high'] > prev['high'] and
            latest['low'] > prev['low']):
            alerts_triggered.append(("Strong bullish candle: Higher High, Higher Low", "SUCCESS"))
        elif (latest['close'] < prev['close'] and
              latest['high'] < prev['high'] and
              latest['low'] < prev['low']):
            alerts_triggered.append(("Strong bearish candle: Lower High, Lower Low", "WARNING"))

    # Volume Spike Alert (simple version)
    if len(data) >= 20:
        recent_volume = sum(d['volume'] for d in data[-5:]) / 5
        avg_volume = sum(d['volume'] for d in data[-20:]) / 20
        if recent_volume > avg_volume * 2:
            alerts_triggered.append(("Volume spike detected: 2x above average", "INFO"))

    # Display alerts
    if alerts_triggered:
        print("🚨 ALERTS TRIGGERED:")
        for message, level in alerts_triggered:
            alert_system.log_alert(f"{symbol}: {message}", level)
    else:
        alert_system.log_alert(f"{symbol}: No significant alerts at this time", "INFO")

    print()
    print("=" * 50)
    print("✅ Analysis complete!")

    # Save history
    alert_system.save_alert_history()

    return alerts_triggered

if __name__ == "__main__":
    # Run the alert system
    alerts = analyze_and_alert('BTCUSDT')

    # Show recent alert history
    print("\n📋 Recent Alert History:")
    alert_system = TradingAlertSystem()
    recent = alert_system.alert_history[-5:] if alert_system.alert_history else []
    for alert in reversed(recent):  # Show newest first
        print(f"   [{alert['timestamp']}] [{alert['level']}] {alert['message']}")