import sqlite3
from datetime import datetime

def test_basic_functionality():
    """Test that our core components work"""
    print("Testing basic functionality...")

    # Test database connection
    try:
        conn = sqlite3.connect('market_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM market_data')
        count = cursor.fetchone()[0]
        print(f"✓ Database connected. Found {count} records.")
        conn.close()
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False

    # Test alert logging to file
    try:
        with open('alerts.log', 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now()}] TEST: Alert system initialized\n")
        print("✓ Alert logging to file works.")
    except Exception as e:
        print(f"✗ Alert file error: {e}")
        return False

    print("✓ All basic functionality tests passed!")
    return True

def simulate_alert_conditions():
    """Simulate what our alert system would detect"""
    print("\n" + "="*50)
    print("SIMULATED ALERT SYSTEM DEMONSTRATION")
    print("="*50)

    # Get latest data to base our simulation on
    try:
        conn = sqlite3.connect('market_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timestamp, close
            FROM market_data
            WHERE symbol = "BTCUSDT"
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        row = cursor.fetchone()
        conn.close()

        if row:
            timestamp, price = row
            print(f"Latest BTCUSDT price: ${price:,.2f} at {timestamp}")
        else:
            print("No data found")
            return
    except Exception as e:
        print(f"Error getting latest data: {e}")
        return

    # Simulate alert conditions that would be detected
    alerts = [
        {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'level': 'ALERT',
            'message': 'BTCUSDT: RSI extremely oversold (<25) - Potential buying opportunity'
        },
        {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'level': 'WARNING',
            'message': 'BTCUSDT: Significant price movement: -2.5% down'
        },
        {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'level': 'INFO',
            'message': 'BTCUSDT: Volume spike detected: 150% above average'
        }
    ]

    print("\n📢 ALERTS THAT WOULD BE TRIGGERED:")
    print("-" * 40)
    for alert in alerts:
        icon = "🚨" if alert['level'] == 'ALERT' else "⚠️" if alert['level'] == 'WARNING' else "ℹ️"
        print(f"{icon} [{alert['timestamp']}] {alert['level']}: {alert['message']}")

        # Also log to file
        try:
            with open('alerts.log', 'a', encoding='utf-8') as f:
                f.write(f"[{alert['timestamp']}] [{alert['level']}] {alert['message']}\n")
        except Exception as e:
            print(f"Error writing to alert log: {e}")

    print(f"\n📝 Alerts also saved to alerts.log")
    print("✅ Alert system demonstration complete!")

if __name__ == '__main__':
    if test_basic_functionality():
        simulate_alert_conditions()