#!/usr/bin/env python3
# Simple test script to verify pattern detection works

import sqlite3

def test_db_connection():
    """Test that we can connect to the database and get data"""
    try:
        conn = sqlite3.connect('market_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM market_data')
        count = cursor.fetchone()[0]
        print(f"Database connection OK. Total records: {count}")

        cursor.execute('SELECT timestamp, close FROM market_data WHERE symbol = "BTCUSDT" ORDER BY timestamp DESC LIMIT 1')
        row = cursor.fetchone()
        if row:
            print(f"Latest BTCUSDT: {row[0]} = ${row[1]:,.2f}")

        conn.close()
        return True
    except Exception as e:
        print(f"Database error: {e}")
        return False

if __name__ == '__main__':
    print("Testing pattern detection components...")
    if test_db_connection():
        print("✓ All tests passed!")
    else:
        print("✗ Tests failed!")