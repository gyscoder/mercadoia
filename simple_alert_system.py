#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime

def get_latest_price():
    """Get the latest BTCUSDT price from database"""
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
            return {"timestamp": row[0], "price": float(row[1])}
        return None
    except Exception as e:
        print(f"Database error: {e}")
        return None

def calculate_rsi_from_db(window=14):
    """Calculate RSI from database data"""
    try:
        conn = sqlite3.connect('market_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT close
            FROM market_data
            WHERE symbol = "BTCUSDT"
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (window + 1,))
        rows = cursor.fetchall()
        conn.close()

        if len(rows) < window + 1:
            return None

        closes = [float(row[0]) for row in reversed(rows)]  # Oldest first

        gains = []
        losses = []
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        avg_gain = sum(gains[-window:]) / window
        avg_loss = sum(losses[-window:]) / window

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    except Exception as e:
        print(f"RSI calculation error: {e}")
        return None

def check_alert_conditions():
    """Check for alert conditions and return alerts"""
    alerts = []

    # Get latest price
    price_data = get_latest_price()
    if not price_data:
        alerts.append(("Unable to fetch price data", "ERROR"))
        return alerts

    # Get RSI
    rsi = calculate_rsi_from_db()

    # Price-based alerts
    price = price_data["price"]
    timestamp = price_data["timestamp"]

    # RSI alerts
    if rsi is not None:
        if rsi < 25:
            alerts.append((f"RSI extremely oversold ({rsi:.1f}) - Strong buying signal", "ALERT"))
        elif rsi < 30:
            alerts.append((f"RSI oversold ({rsi:.1f}) - Potential bounce", "WARNING"))
        elif rsi > 75:
            alerts.append((f"RSI extremely overbought ({rsi:.1f}) - Strong selling signal", "ALERT"))
        elif rsi > 70:
            alerts.append((f"RSI overbought ({rsi:.1f}) - Consider taking profits", "WARNING"))

    # Simple price change alert (compare to previous period)
    try:
        conn = sqlite3.connect('market_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT close
            FROM market_data
            WHERE symbol = "BTCUSDT"
            ORDER BY timestamp DESC
            LIMIT 2
        ''')
        rows = cursor.fetchall()
        conn.close()

        if len(rows) >= 2:
            current_price = float(rows[0][0])
            previous_price = float(rows[1][0])
            change_pct = ((current_price - previous_price) / previous_price) * 100

            if abs(change_pct) > 2.0:  # More than 2% change
                direction = "up" if change_pct > 0 else "down"
                alerts.append((f"Price {direction}: {change_pct:+.2f}% in last period", "WARNING"))
    except Exception as e:
        print(f"Price change check error: {e}")

    return alerts

def log_alert_to_console_and_file(alerts):
    """Log alerts to console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not alerts:
        msg = f"[{timestamp}] No alerts at this time"
        print(msg)
        try:
            with open("alerts.log", "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except Exception as e:
            print(f"Error writing to log file: {e}")
        return

    for message, level in alerts:
        # Console output with emojis
        if level == "ALERT":
            icon = "🚨"
        elif level == "WARNING":
            icon = "⚠️"
        elif level == "ERROR":
            icon = "❌"
        else:
            icon = "ℹ️"

        console_msg = f"[{timestamp}] {icon} {level}: {message}"
        print(console_msg)

        # File output
        try:
            with open("alerts.log", "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [{level}] {message}\n")
        except Exception as e:
            print(f"Error writing to log file: {e}")

def main():
    """Main function to run the alert system"""
    print("=" * 50)
    print("🤖 BOT DE INVESTIMENTOS - SISTEMA DE ALERTAS")
    print("=" * 50)

    # Check alert conditions
    alerts = check_alert_conditions()

    # Log alerts
    log_alert_to_console_and_file(alerts)

    print("=" * 50)
    print("✅ Verificação de alertas concluída")
    print("📋 Alertas também foram salvos em alerts.log")

if __name__ == "__main__":
    main()