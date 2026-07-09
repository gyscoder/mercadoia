#!/usr/bin/env python3
# Simple test script to verify basic functionality

import sqlite3
import sys

print("Python version:", sys.version)
print("Testing SQLite connection...")

try:
    conn = sqlite3.connect('market_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM market_data")
    count = cursor.fetchone()[0]
    print(f"Successfully connected to database. Total records: {count}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

print("Test completed successfully!")