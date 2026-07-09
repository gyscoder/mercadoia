import sqlite3
import pandas as pd
from detect_patterns_with_alerts import calculate_rsi

def get_all_historical_data(symbol='BTCUSDT', interval='1h'):
    conn = sqlite3.connect('market_data.db')
    query = '''
    SELECT timestamp, open, high, low, close, volume
    FROM market_data
    WHERE symbol = ? AND interval = ?
    ORDER BY timestamp ASC
    '''
    df = pd.read_sql_query(query, conn, params=(symbol, interval))
    conn.close()
    return df

def calculate_sma(prices, period=200):
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def simulate_strategy_v3_classic(df, take_profit, stop_loss):
    """Simulação pura da V3 Campeã: SMA 200 + RSI < 30 + Gatilho de Máxima Anterior"""
    capital_inicial = 1000.0
    capital = capital_inicial
    posicao = 0.0
    em_posicao = False
    preco_compra = 0.0
    
    total_trades = 0
    trades_ganhos = 0

    closes = df['close'].astype(float).tolist()
    highs = df['high'].astype(float).tolist()

    for i in range(200, len(df)):
        dados_ate_agora = closes[:i+1]
        preco_atual = closes[i]
        maxima_anterior = highs[i-1]

        rsi = calculate_rsi(dados_ate_agora)
        sma200 = calculate_sma(dados_ate_agora, period=200)
        
        if rsi is None or sma200 is None:
            continue

        if em_posicao:
            variacao_preco = (preco_atual - preco_compra) / preco_compra
            
            if variacao_preco >= take_profit:
                capital = posicao * preco_atual
                trades_ganhos += 1
                em_posicao = False
                posicao = 0.0
                total_trades += 1
            elif variacao_preco <= -stop_loss:
                capital = posicao * preco_atual
                em_posicao = False
                posicao = 0.0
                total_trades += 1
        else:
            # Lógica de Equilíbrio V3
            if rsi < 30 and preco_atual > sma200:
                if preco_atual > maxima_anterior:
                    posicao = capital / preco_atual
                    preco_compra = preco_atual
                    capital = 0.0
                    em_posicao = True

    if em_posicao:
        preco_final = closes[-1]
        capital = posicao * preco_final
        if preco_final > preco_compra:
            trades_ganhos += 1
        total_trades += 1

    retorno_total = ((capital - capital_inicial) / capital_inicial) * 100
    win_rate = (trades_ganhos / total_trades * 100) if total_trades > 0 else 0
    
    return retorno_total, total_trades, win_rate

def run_final_optimization():
    print("=== INICIANDO AJUSTE FINO FINAL DA V3 CLÁSSICA ===")
    df = get_all_historical_data()
    
    if df.empty or len(df) < 250:
        print("Dados insuficientes no banco.")
        return

    # Testando alvos mais cirúrgicos e velozes
    take_profit_options = [0.01, 0.015, 0.02, 0.03]
    stop_loss_options = [0.005, 0.0075, 0.01, 0.015]
    
    resultados = []

    for tp in take_profit_options:
        for sl in stop_loss_options:
            retorno, trades, wr = simulate_strategy_v3_classic(df, tp, sl)
            resultados.append({
                'TP %': tp * 100,
                'SL %': sl * 100,
                'Retorno %': retorno,
                'Total Trades': trades,
                'Win Rate %': wr
            })
    
    df_res = pd.DataFrame(resultados)
    df_res = df_res.sort_values(by='Retorno %', ascending=False)
    
    print("\n================ RANKING FINAL DE CONFIGURAÇÕES V3 ================")
    print(df_res.to_string(index=False, formatters={
        'Retorno %': '{:+.2f}%'.format,
        'Win Rate %': '{:.2f}%'.format
    }))
    print("===================================================================")

if __name__ == '__main__':
    run_final_optimization()