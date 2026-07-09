import datetime

class SimpleAlertSystem:
    def __init__(self):
        self.alert_history = []

    def log_alert(self, message, level="INFO"):
        """Log an alert with timestamp"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alert = {
            'timestamp': timestamp,
            'level': level,
            'message': message
        }
        self.alert_history.append(alert)

        # Print to console with color-like indicators
        if level == "ALERT":
            print(f"[{timestamp}] 🚨 ALERT: {message}")
        elif level == "WARNING":
            print(f"[{timestamp}] ⚠️  WARNING: {message}")
        else:
            print(f"[{timestamp}] ℹ️  INFO: {message}")

    def get_recent_alerts(self, count=10):
        """Get recent alerts"""
        return self.alert_history[-count:] if self.alert_history else []

def check_for_alert_conditions(pattern_data):
    """Check if any alert conditions are met based on pattern analysis"""
    alerts = []

    # Extract data from pattern analysis (this would come from our detection function)
    # For now, we'll simulate based on what we know from the last run
    signals = pattern_data.get('signals', [])
    assessment = pattern_data.get('assessment', 'NEUTRAL')
    rsi = pattern_data.get('rsi', 50)

    # Alert conditions
    if 'RSI_OVERSOLD' in signals and rsi < 25:
        alerts.append(("RSI extremely oversold (<25)", "ALERT"))
    elif 'RSI_OVERBOUGHT' in signals and rsi > 75:
        alerts.append(("RSI extremely overbought (>75)", "ALERT"))

    if 'TREND_DOWN_STRONG' in signals and 'TREND_UP_STRONG' in signals:
        alerts.append(("Conflicting strong signals detected", "WARNING"))

    if assessment == "BEARISH" and 'RSI_OVERSOLD' in signals:
        alerts.append(("Bearish market with oversold conditions - potential reversal", "WARNING"))
    elif assessment == "BULLISH" and 'RSI_OVERBOUGHT' in signals:
        alerts.append(("Bullish market with overbought conditions - potential pullback", "WARNING"))

    return alerts

def create_alert_system_integration():
    """Create an integrated version that works with our pattern detection"""

    # This is what we would add to our detect_patterns_simple_fixed.py
    alert_system = SimpleAlertSystem()

    # Example usage based on our last run:
    sample_data = {
        'symbol': 'BTCUSDT',
        'timestamp': '2026-06-22T18:00:00',
        'price': 64286.00,
        'signals': ['TREND_DOWN_STRONG', 'RSI_OVERSOLD', 'PRICE_UP'],
        'assessment': 'NEUTRAL',
        'rsi': 27.16
    }

    # Check for alerts
    alerts = check_for_alert_conditions(sample_data)

    if alerts:
        alert_system.log_alert(f"Analysis for {sample_data['symbol']}: {sample_data['price']:,.2f}", "INFO")
        for msg, level in alerts:
            alert_system.log_alert(msg, level)
    else:
        alert_system.log_alert(f"No alert conditions for {sample_data['symbol']}", "INFO")

    return alert_system

if __name__ == "__main__":
    print("Testing Alert System Integration...")
    alert_sys = create_alert_system_integration()
    print(f"\nAlert history: {len(alert_sys.alert_history)} alerts recorded")
    for alert in alert_sys.alert_history[-3:]:  # Show last 3
        print(f"  [{alert['timestamp']}] {alert['level']}: {alert['message']}")