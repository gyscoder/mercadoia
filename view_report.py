import sqlite3
import pandas as pd
import time
import os
from config import WATCHLIST, DB_NAME

def show_trade_report():
    conn = sqlite3.connect(DB_NAME)
    try:
        df_history = pd.read_sql_query("SELECT * FROM trade_history ORDER BY id DESC", conn)
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM bot_state")
        estados = dict(cursor.fetchall())
    except Exception as e:
        print(f"Aguardando dados... (Erro: {e})")
        conn.close()
        return
    conn.close()

    # --- EXIBIÇÃO NO TERMINAL ---
    print("\n================ STATUS ATUAL POR MOEDA ================")
    for symbol in WATCHLIST:
        em_pos = estados.get(f"{symbol}_em_posicao", 'False')
        preco_in = estados.get(f"{symbol}_preco_compra", '0.0')
        print(f"{symbol.ljust(9)} | Em Posição: {em_pos:<5} | Entrada: ${float(preco_in):,.2f}")

    print("\n================ HISTORICO DE TRADES ================")
    if df_history.empty:
        print("Nenhum trade fechado ainda.")
    else:
        print(df_history.head(10).to_string(index=False, formatters={
            'preco_entrada': '${:,.2f}'.format,
            'preco_saida': '${:,.2f}'.format,
            'resultado_pct': '{:+.2f}%'.format
        }))
        
        # Resumo
        lucro_acumulado = df_history['resultado_pct'].sum()
        print(f"\nLucro Acumulado: {lucro_acumulado:+.2f}%")
    print("=======================================================\n")

if __name__ == '__main__':
    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"Monitorando em tempo real... (Pressione Ctrl+C para sair)")
            show_trade_report()
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nMonitoramento encerrado pelo usuário. Até logo!")