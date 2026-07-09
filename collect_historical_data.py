import sqlite3
import requests
from datetime import datetime, timedelta
import time

def init_db():
    conn = sqlite3.connect('market_data.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS market_data (
        symbol TEXT,
        interval TEXT,
        timestamp TEXT,
        open TEXT,
        high TEXT,
        low TEXT,
        close TEXT,
        volume TEXT,
        PRIMARY KEY (symbol, interval, timestamp)
    )
    ''')
    conn.commit()
    conn.close()

def fetch_historical_chunk(symbol, interval, start_time_ms):
    """Puxa um bloco de ate 1000 velas a partir de um timestamp especifico"""
    url = "https://api.binance.com/api/v3/klines"
    params = {
        'symbol': symbol,
        'interval': interval,
        'startTime': start_time_ms,
        'limit': 1000
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro na API Binance: Status {response.status_code}")
            return []
    except Exception as e:
        print(f"Erro na requisicao: {e}")
        return []

def collect_mass_data(symbol='BTCUSDT', interval='1h', days_back=60):
    print(f"=== INICIANDO COLETA EM MASSA DO HISTORICO ({days_back} DIAS) ===")
    init_db()
    
    # Calcula o timestamp de inicio (em milissegundos)
    start_date = datetime.now() - timedelta(days=days_back)
    current_start_ms = int(start_date.timestamp() * 1000)
    end_ms = int(time.time() * 1000)
    
    conn = sqlite3.connect('market_data.db')
    cursor = conn.cursor()
    
    total_inserted = 0
    
    while current_start_ms < end_ms:
        readable_date = datetime.fromtimestamp(current_start_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')
        print(f"Buscando dados a partir de: {readable_date}...")
        
        klines = fetch_historical_chunk(symbol, interval, current_start_ms)
        
        if not klines:
            print("Nenhum dado retornado ou fim do historico atingido.")
            break
            
        chunk_inserted = 0
        for candle in klines:
            # Converte o timestamp do candle (ms) para string legivel ISO
            candle_time = datetime.fromtimestamp(candle[0] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            
            query = '''
            INSERT OR IGNORE INTO market_data (symbol, interval, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            '''
            cursor.execute(query, (
                symbol, interval, candle_time,
                str(candle[1]), str(candle[2]), str(candle[3]), str(candle[4]), str(candle[5])
            ))
            if cursor.rowcount > 0:
                chunk_inserted += 1
        
        conn.commit()
        total_inserted += chunk_inserted
        print(f"Inseridos {chunk_inserted} novos registros neste bloco.")
        
        # O ultimo candle do bloco atual serve como o startTime do proximo bloco
        last_candle_ms = klines[-1][0]
        
        # Segurança para evitar loop infinito se a API parar de avançar o tempo
        if last_candle_ms <= current_start_ms:
            break
            
        current_start_ms = last_candle_ms + 1
        time.sleep(0.5)  # Evita tomar block por excesso de requisicoes
        
    conn.close()
    print(f"\n=== COLETA CONCLUIDA: {total_inserted} registros adicionados ao banco ===")

if __name__ == '__main__':
    # Vamos buscar os ultimos 60 dias para um teste ultra robusto
    collect_mass_data(symbol='BTCUSDT', interval='1h', days_back=60)