import json
import os
from datetime import datetime
from typing import Dict, List

class AlertSystem:
    def __init__(self, alert_file: str = "alerts.log"):
        self.alert_file = alert_file
        self.alerts_sent = set()  # Track alert hashes to avoid duplicates

    def log_alert(self, message: str, level: str = "INFO"):
        """Log alert to console and file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"[{timestamp}] [{level}] {message}"

        # Print to console with emoji indicators
        if level == "ALERT":
            print(f"🚨 {formatted_msg}")
        elif level == "WARNING":
            print(f"⚠️  {formatted_msg}")
        elif level == "SUCCESS":
            print(f"✅ {formatted_msg}")
        else:
            print(f"ℹ️  {formatted_msg}")

        # Write to file
        try:
            with open(self.alert_file, "a", encoding="utf-8") as f:
                f.write(formatted_msg + "\n")
        except Exception as e:
            print(f"Error writing to alert file: {e}")

    def should_send_alert(self, alert_key: str) -> bool:
        """Check if we should send this alert (avoid duplicates)"""
        if alert_key in self.alerts_sent:
            return False
        self.alerts_sent.add(alert_key)
        # Keep only last 100 alerts in memory to prevent unbounded growth
        if len(self.alerts_sent) > 100:
            # Keep most recent 50
            self.alerts_sent = set(list(self.alerts_sent)[-50:])
        return True

def format_trading_signal(signal_data: Dict) -> tuple[str, str]:
    """Format trading signal into a readable alert message and determine level"""
    symbol = signal_data.get('symbol', 'UNKNOWN')
    price = float(signal_data.get('price', 0))
    change = float(signal_data.get('change_percent', 0))
    rsi = float(signal_data.get('rsi', 0))
    signals = signal_data.get('signals', [])
    assessment = signal_data.get('assessment', 'NEUTRAL')

    # Determine alert level based on signals
    alert_level = "INFO"
    bullish_signals = ['OVERSOLD', 'STRONG_BULL', 'BULLISH', 'TREND_UP', 'STRONG_UPTREND', 'PRICE_UP', 'PRICE_STRONG_BULL']
    bearish_signals = ['OVERBOUGHT', 'STRONG_BEAR', 'BEARISH', 'TREND_DOWN', 'STRONG_DOWNTREND', 'PRICE_DOWN', 'PRICE_STRONG_BEAR']

    has_bullish = any(any(b in s for b in bullish_signals) for s in signals)
    has_bearish = any(any(b in s for b in bearish_signals) for s in signals)
    has_strong = any('STRONG' in s for s in signals)

    if has_strong:
        alert_level = "ALERT"
    elif has_bullish and not has_bearish:
        alert_level = "SUCCESS"
    elif has_bearish and not has_bullish:
        alert_level = "WARNING"

    # Build message
    price_str = f"${price:,.2f}"
    change_str = f"{change:+.2f}%"
    rsi_str = f"RSI: {rsi:.1f}"

    # Show first 3 signals for brevity
    signals_str = ", ".join(signals[:3])
    if len(signals) > 3:
        signals_str += f" (+{len(signals)-3} more)"

    message = (
        f"{symbol} Alert: {price_str} ({change_str}) | {rsi_str} | {assessment} | "
        f"Signals: {signals_str}"
    )

    return message, alert_level

# Example usage function
def check_and_alert(signal_data: Dict, alert_system: AlertSystem) -> bool:
    """Check trading data and send alerts if conditions are met.
    Returns True if alert was sent, False if skipped (duplicate)."""
    # Create a unique key for this alert based on timestamp and signals
    signal_tuple = tuple(sorted(signal_data.get('signals', [])))
    alert_key = f"{signal_data.get('timestamp', '')}_{hash(signal_tuple)}"

    if not alert_system.should_send_alert(alert_key):
        return False  # Skip duplicate alerts

    message, level = format_trading_signal(signal_data)
    alert_system.log_alert(message, level)
    return True

if __name__ == "__main__":
    # Test the alert system
    alert_sys = AlertSystem()

    # Sample data based on our last run
    test_data = {
        'symbol': 'BTCUSDT',
        'timestamp': '2026-06-22 18:00:00',
        'price': 64286.00,
        'change_percent': 0.04,
        'rsi': 27.16,
        'signals': ['TREND_DOWN_STRONG', 'RSI_OVERSOLD', 'PRICE_UP'],
        'assessment': 'NEUTRAL'
    }

    print("Testing alert system...")
    sent = check_and_alert(test_data, alert_sys)
    if sent:
        print("Alert sent!")
    else:
        print("Alert skipped (duplicate)")