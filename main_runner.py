import time
import requests
import sqlite3
import pandas as pd
from datetime import datetime
from detect_patterns_with_alerts import calculate_rsi
from config import WATCHLIST, TAKE_PROFIT_PCT, STOP_LOSS_PCT, INTERVALO_MONITORAMENTO, DB_NAME, LOG_FILE

# Configurações do Assistente de Análise
WATCHLIST = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
TAKE_PROFIT_PCT = 0.02
STOP_LOSS_PCT = 0.0075
INTERVALO_MONITORAMENTO = 3  # Segundos entre varreduras do mercado

def log_sistema_erro(mensagem):
    """Grava erros de rede ou API em um arquivo local permanente"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open("erros_sistema.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {mensagem}\n")

def init_trading_tables():
    conn = sqlite3.connect('market_data.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bot_state (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trade_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        symbol TEXT,
        tipo TEXT,
        preco_entrada REAL,
        preco_saida REAL,
        resultado_pct REAL
    )
    ''')
    conn.commit()
    conn.close()

def save_state(symbol, em_posicao, preco_compra):
    conn = sqlite3.connect('market_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO bot_state (key, value) VALUES (?, ?)", (f"{symbol}_em_posicao", str(em_posicao)))
    cursor.execute("INSERT OR REPLACE INTO bot_state (key, value) VALUES (?, ?)", (f"{symbol}_preco_compra", str(preco_compra)))
    conn.commit()
    conn.close()

def load_state(symbol):
    conn = sqlite3.connect('market_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM bot_state WHERE key = ?", (f"{symbol}_em_posicao",))
    res_pos = cursor.fetchone()
    cursor.execute("SELECT value FROM bot_state WHERE key = ?", (f"{symbol}_preco_compra",))
    res_preco = cursor.fetchone()
    conn.close()
    
    # Se o banco estiver vazio ou não encontrar o registro, o padrão SEMPRE será False e 0.0
    if not res_pos or res_pos[0] is None:
        return False, 0.0
        
    em_posicao = str(res_pos[0]).strip() == 'True'
    preco_compra = float(res_preco[0]) if res_preco and res_preco[0] else 0.0
    return em_posicao, preco_compra

def log_trade(symbol, tipo, preco_entrada, preco_saida, resultado_pct):
    conn = sqlite3.connect('market_data.db')
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
    INSERT INTO trade_history (timestamp, symbol, tipo, preco_entrada, preco_saida, resultado_pct)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (timestamp, symbol, tipo, preco_entrada, preco_saida, resultado_pct))
    conn.commit()
    conn.close()

def get_live_candles(symbol, interval='1m', limit=250):
    url = f"https://api.binance.com/api/v3/klines"
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    
    # Nova lógica de repetição (Retry)
    for tentativa in range(3): 
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                log_sistema_erro(f"Erro API Binance para {symbol}: HTTP {response.status_code}")
                break # Se for erro 400/404, não adianta insistir
        except requests.exceptions.RequestException as e:
            log_sistema_erro(f"Conexão falhou para {symbol} (Tentativa {tentativa+1}/3): {str(e)}")
            time.sleep(2) # Espera 2 segundos antes de tentar de novo
            
    return None

def calculate_sma(prices, period=200):
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def monitor_watchlist():
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n================ VARREDURA DA WATCHLIST [{timestamp}] ================", flush=True)
    
    for symbol in WATCHLIST:
        em_posicao, preco_compra = load_state(symbol)
        klines = get_live_candles(symbol)
        if not klines:
            continue

        closes = [float(candle[4]) for candle in klines]
        highs = [float(candle[2]) for candle in klines]
        volumes = [float(candle[5]) for candle in klines] 
        
        preco_atual = closes[-1]
        maxima_anterior = highs[-2]
        volume_atual = float(klines[-1][5])
        media_volume = sum(volumes[-21:-1]) / 20 
        
        rsi = calculate_rsi(closes)
        sma200 = calculate_sma(closes, period=200)
        
        if rsi is None or sma200 is None:
            continue

        # Lógica de Status com SMA 200 integrada na visualização
        if em_posicao:
            status_pos = "$$ COMPRADO (Gerenciando...)"
        elif rsi < 30 and preco_atual > sma200 and volume_atual > (media_volume * 1.2):
            status_pos = f"!! ALERTA (Tendência Alta! Aguardando rompimento)"
        else:
            status_pos = ".::|BUSCANDO|::."

        # Tabela com Preço, SMA 200, RSI e Volume
        print(f"{symbol.ljust(9)} | P: {preco_atual:<8,.2f} | SMA200: {sma200:<8,.2f} | RSI: {rsi:<5.2f} | Vol: {volume_atual:.0f} | Status: {status_pos}", flush=True)

        # Regra de Entrada com Filtro de Volume e SMA 200
        # Regra de Entrada com Diagnóstico de Filtros
        # REGRA DE ENTRADA OTIMIZADA (Mais agressiva)
        if not em_posicao:
            distancia_sma = ((preco_atual - sma200) / sma200) * 100
            if -2.0 < distancia_sma < 0:
                print(f"-> {symbol}: [APROXIMAÇÃO] Está a {distancia_sma:.2f}% da SMA200. Monitorando...")
            # 1. Filtro de Tendência (Obrigatório)
            cond_sma = preco_atual > sma200
            # 2. Filtro de Volume (Basta ser maior que a média)
            cond_vol = volume_atual > media_volume
            
            # Diagnosticamos se ele ainda estiver "mudo"
            if cond_sma and cond_vol:
                # Se o preço superou a média e o volume está acima da média, COMPRA.
                # Removemos o filtro de RSI e a máxima anterior para não travar a entrada.
                preco_compra = preco_atual
                em_posicao = True
                save_state(symbol, em_posicao, preco_compra)
                print(f"\n!!! COMPRA AGRESSIVA CONFIRMADA EM {symbol} !!!")
            else:
                # O que está faltando?
                motivos = []
                if not cond_sma: motivos.append("Preço < SMA200")
                if not cond_vol: motivos.append("Volume Fraco")
                print(f"-> {symbol}: Aguardando... ({', '.join(motivos)})")
        
        # Gerenciamento de Risco com Trailing Stop
        else:
            variacao = (preco_atual - preco_compra) / preco_compra
            
            # Trailing Stop: Se lucro >= 1%, o stop vai para o preço de entrada. 
            # Depois, mantém distância de 0.5% do preço atual.
            stop_dinamico = preco_compra if variacao < 0.01 else (preco_atual * 0.995)
            
            if preco_atual <= stop_dinamico and variacao > 0.005:
                print(f"\n!!! TRAILING STOP ATINGIDO EM {symbol} !!!")
                log_trade(symbol, "TRAILING_STOP", preco_compra, preco_atual, variacao * 100)
                save_state(symbol, False, 0.0)
            elif variacao >= TAKE_PROFIT_PCT:
                print(f"\n!!! TAKE PROFIT FIXO ATINGIDO EM {symbol} !!!")
                log_trade(symbol, "TAKE_PROFIT", preco_compra, preco_atual, 2.0)
                save_state(symbol, False, 0.0)
            elif variacao <= -STOP_LOSS_PCT:
                print(f"\n!!! STOP LOSS ATINGIDO EM {symbol} !!!")
                log_trade(symbol, "STOP_LOSS", preco_compra, preco_atual, -0.75)
                save_state(symbol, False, 0.0)

if __name__ == '__main__':
    print("=== ASSISTENTE MULTIMOEDAS PERSISTENTE INICIADO ===")
    init_trading_tables()
    
    try:
        while True:
            monitor_watchlist()
            time.sleep(INTERVALO_MONITORAMENTO)
    except KeyboardInterrupt:
        print("\nAssistente finalizado pelo usuário.")