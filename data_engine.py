import sqlite3, requests, time
from datetime import datetime
from config import DB_NAME, LOG_FILE
import time
from functools import wraps

def retry_on_failure(retries=3, delay=5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for i in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    print(f"Erro na conexão, tentando novamente em {delay}s... ({i+1}/{retries})")
                    time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator

def log_sistema_erro(mensagem):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {mensagem}\n")

def init_trading_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Tabela de estado do bot
    cursor.execute("CREATE TABLE IF NOT EXISTS bot_state (key TEXT PRIMARY KEY, value TEXT)")
    # Tabela de comandos
    cursor.execute("CREATE TABLE IF NOT EXISTS commands (id INTEGER PRIMARY KEY AUTOINCREMENT, cmd TEXT)")
    # Tabela de histórico corrigida (com as colunas que o seu código espera)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trade_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            timestamp TEXT,
            symbol TEXT, 
            tipo TEXT, 
            preco_entrada REAL, 
            preco_saida REAL, 
            resultado_pct REAL
        )
    """)
    conn.commit()
    conn.close()

def save_state(symbol, em_posicao, preco_compra):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO bot_state (key, value) VALUES (?, ?)", (f"{symbol}_em_posicao", str(em_posicao)))
    cursor.execute("INSERT OR REPLACE INTO bot_state (key, value) VALUES (?, ?)", (f"{symbol}_preco_compra", str(preco_compra)))
    conn.commit()
    conn.close()

def load_state(symbol):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM bot_state WHERE key = ?", (f"{symbol}_em_posicao",))
    res_pos = cursor.fetchone()
    cursor.execute("SELECT value FROM bot_state WHERE key = ?", (f"{symbol}_preco_compra",))
    res_preco = cursor.fetchone()
    conn.close()
    if not res_pos or res_pos[0] is None: return False, 0.0
    return str(res_pos[0]).strip() == 'True', float(res_preco[0]) if res_preco else 0.0

def log_trade(symbol, tipo, preco_entrada, preco_saida, resultado_pct):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('INSERT INTO trade_history (timestamp, symbol, tipo, preco_entrada, preco_saida, resultado_pct) VALUES (?, ?, ?, ?, ?, ?)', (timestamp, symbol, tipo, preco_entrada, preco_saida, resultado_pct))
    conn.commit()
    conn.close()

@retry_on_failure(retries=5, delay=10)
def get_live_candles(symbol, interval='1m', limit=250):
    url = "https://api.binance.com/api/v3/klines"
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    
    # O decorador vai tentar executar o bloco abaixo 5 vezes
    response = requests.get(url, params=params, timeout=10)
    
    if response.status_code == 200:
        return response.json()
    else:
        # Se o status não for 200 (ex: 429 - Too Many Requests), 
        # levantamos um erro para o decorador capturar e tentar novamente
        raise Exception(f"Erro na API Binance: {response.status_code} - {response.text}")

def check_for_commands():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Pega o último comando inserido
    cursor.execute("SELECT id, cmd FROM commands ORDER BY id DESC LIMIT 1")
    res = cursor.fetchone()
    
    comando = None
    if res:
        cmd_id, comando = res
        # DELETA o comando para ele não ficar preso no banco
        cursor.execute("DELETE FROM commands WHERE id = ?", (cmd_id,))
        conn.commit()
    
    conn.close()
    return comando