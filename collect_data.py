import requests
import sqlite3
import time
from datetime import datetime

def create_connection(db_file):
    """Create a database connection to the SQLite database specified by db_file"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

def create_table(conn):
    """Create table for market data if it doesn't exist"""
    try:
        sql_create_market_data_table = """
        CREATE TABLE IF NOT EXISTS market_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,  -- Store as ISO format string to avoid deprecation warning
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume REAL NOT NULL,
            symbol TEXT NOT NULL,
            interval TEXT NOT NULL
        );
        """
        cursor = conn.cursor()
        cursor.execute(sql_create_market_data_table)
    except sqlite3.Error as e:
        print(e)

def insert_market_data(conn, data):
    """Insert a new market data record"""
    sql = ''' INSERT INTO market_data(timestamp,open,high,low,close,volume,symbol,interval)
              VALUES(?,?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, data)
    conn.commit()
    return cur.lastrowid

def fetch_binance_klines(symbol='BTCUSDT', interval='1h', limit=100):
    """Fetch klines/candlestick data from Binance API"""
    url = f'https://api.binance.com/api/v3/klines'
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Binance: {e}")
        return None

def main():
    # Configuration
    SYMBOL = 'BTCUSDT'
    INTERVAL = '1h'
    LIMIT = 100  # Number of klines to fetch
    DB_NAME = 'market_data.db'

    # Fetch data from Binance
    print(f"Fetching {LIMIT} {INTERVAL} klines for {SYMBOL} from Binance...")
    klines = fetch_binance_klines(SYMBOL, INTERVAL, LIMIT)

    if klines is None:
        print("Failed to fetch data. Exiting.")
        return

    # Set up database
    conn = create_connection(DB_NAME)
    if conn is None:
        print("Error! Cannot create database connection.")
        return

    create_table(conn)

    # Process and store each kline
    for kline in klines:
        # Binance kline format:
        # [0] Open time
        # [1] Open
        # [2] High
        # [3] Low
        # [4] Close
        # [5] Volume
        # [6] Close time
        # [7] Quote asset volume
        # [8] Number of trades
        # [9] Taker buy base asset volume
        # [10] Taker buy quote asset volume
        # [11] Ignore

        timestamp = datetime.fromtimestamp(kline[0]/1000)  # Convert to seconds
        # Store timestamp as ISO format string to avoid deprecation warning in Python 3.12+
        timestamp_str = timestamp.isoformat()
        open_price = float(kline[1])
        high_price = float(kline[2])
        low_price = float(kline[3])
        close_price = float(kline[4])
        volume = float(kline[5])

        data = (timestamp_str, open_price, high_price, low_price, close_price, volume, SYMBOL, INTERVAL)
        insert_market_data(conn, data)

    print(f"Successfully stored {len(klines)} records in {DB_NAME}")

    # Verify by reading back
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM market_data")
    count = cursor.fetchone()[0]
    print(f"Total records in database: {count}")

    conn.close()

if __name__ == '__main__':
    main()