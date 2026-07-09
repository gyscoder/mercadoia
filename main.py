import time
from datetime import datetime
from config import WATCHLIST, TAKE_PROFIT_PCT, STOP_LOSS_PCT, INTERVALO_MONITORAMENTO, VOL_MULTIPLIER
from data_engine import init_trading_tables, get_live_candles, load_state, save_state, log_trade, check_for_commands
from strategy import calcular_decisao
from detect_patterns_with_alerts import calculate_rsi

def main():
    print("=== ASSISTENTE MULTIMOEDAS PERSISTENTE INICIADO ===")
    init_trading_tables()
    
    try:
        while True:
            comando = check_for_commands()
            if comando == "PAUSAR":
                print("\n>>> ROBÔ PAUSADO. Aguardando comando de RESUMIR...")
                while True:
                    time.sleep(2)
                    # Verifica se o painel enviou o comando de RESUMIR
                    if check_for_commands() == "RESUMIR":
                        print(">>> RESUMINDO OPERAÇÕES.")
                        break

            elif comando == "VENDA_TOTAL":
                print("\n!!! COMANDO DE EMERGÊNCIA: VENDENDO TUDO !!!")
                for symbol in WATCHLIST:
                    em_pos, preco_in = load_state(symbol)
                    if em_pos:
                        preco_atual = float(get_live_candles(symbol)[-1][4])
                        log_trade(symbol, "EMERGENCIA", preco_in, preco_atual, 0.0)
                        save_state(symbol, False, 0.0)
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n================ VARREDURA DA WATCHLIST [{timestamp}] ================", flush=True)
            
            for symbol in WATCHLIST:
                em_posicao, preco_compra = load_state(symbol)
                klines = get_live_candles(symbol)
                if not klines: continue

                # Extração de dados
                closes = [float(k[4]) for k in klines]
                volumes = [float(k[5]) for k in klines]
                preco_atual = closes[-1]
                sma200 = sum(closes[-200:]) / 200
                rsi = calculate_rsi(closes)
                
                # Definição do status para a exibição
                status_pos = "$$ COMPRADO (Gerenciando...)" if em_posicao else ".::|BUSCANDO|::."
                
                # Print formatado igual ao seu antigo
                print(f"{symbol.ljust(9)} | P: {preco_atual:<8,.2f} | SMA200: {sma200:<8,.2f} | RSI: {rsi:<5.2f} | Vol: {int(volumes[-1])} | Status: {status_pos}", flush=True)

                # Lógica de decisão
                comando, resultado = calcular_decisao(
                    preco_atual, sma200, volumes[-1], sum(volumes[-21:-1])/20, 
                    em_posicao, preco_compra, rsi, TAKE_PROFIT_PCT, STOP_LOSS_PCT
                )

                status_log = f"Status: {comando} | RSI: {rsi:.2f} | Filtro Vol: {volumes[-1] > (sum(volumes[-21:-1])/20 * VOL_MULTIPLIER)}"
                with open("robo_debug.log", "a") as f:
                    f.write(f"{timestamp} | {symbol} | {status_log}\n")
                
                if comando == "COMPRA":
                    save_state(symbol, True, resultado)
                    print(f"\n!!! COMPRA CONFIRMADA EM {symbol} !!!")
                elif comando == "VENDA":
                    tipo, pct = resultado
                    log_trade(symbol, tipo, preco_compra, preco_atual, pct)
                    save_state(symbol, False, 0.0)
                    print(f"\n!!! VENDA ({tipo}) EM {symbol} !!!")
            
            time.sleep(INTERVALO_MONITORAMENTO)
    except KeyboardInterrupt:
        print("\nAssistente finalizado pelo usuário.")

if __name__ == '__main__':
    main()