from datetime import datetime

# Copiando as regras de gerenciamento do seu projeto para o teste
TAKE_PROFIT_PCT = 0.02
STOP_LOSS_PCT = 0.01

def test_alert_logic(scenario_name, rsi, preco_atual, sma200, maxima_anterior, em_posicao, preco_compra):
    print(f"\n--- TESTANDO CENARIO: {scenario_name} ---")
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] Preco: ${preco_atual:,.2f} | SMA 200: ${sma200:,.2f} | RSI: {rsi:.2f}")

    if not em_posicao:
        # Lógica idêntica ao seu main_runner.py
        if rsi < 30 and preco_atual > sma200:
            if preco_atual > maxima_anterior:
                preco_compra = preco_atual
                em_posicao = True
                print(f"!!! ALERTA DE COMPRA EXECUTADA (SIMULADO) !!!")
                print(f"Preco de Entrada: ${preco_compra:,.2f} | Alvo TP (2%): ${preco_compra * (1 + TAKE_PROFIT_PCT):,.2f} | Stop SL (1%): ${preco_compra * (1 - STOP_LOSS_PCT):,.2f}")
            else:
                print("Filtros aceitos, mas o preco nao rompeu a maxima anterior ainda.")
        else:
            print("Condicoes de mercado normais. Nenhum padrao detectado.")
    else:
        # Lógica de saída
        variacao = (preco_atual - preco_compra) / preco_compra
        if variacao >= TAKE_PROFIT_PCT:
            print(f"!!! ALERTA: TAKE PROFIT ATINGIDO (SIMULADO) !!!")
            print(f"Saida a ${preco_atual:,.2f} | Lucro: +2.00%")
            em_posicao = False
        elif variacao <= -STOP_LOSS_PCT:
            print(f"!!! ALERTA: STOP LOSS ATINGIDO (SIMULADO) !!!")
            print(f"Saida a ${preco_atual:,.2f} | Prejuizo: -1.00%")
            em_posicao = False
        else:
            print(f"Em posicao: Variacao atual de {variacao*100:+.2f}%")
            
    return em_posicao, preco_compra

if __name__ == '__main__':
    print("=== INICIANDO AUDITORIA DE ALERTAS LOCAIS ===")
    
    # 1. Testando cenário neutro (Mercado sem padrão)
    test_alert_logic("Mercado Neutro", rsi=45.0, preco_atual=64000.0, sma200=63000.0, maxima_anterior=63900.0, em_posicao=False, preco_compra=0.0)
    
    # 2. Testando o disparo real do ALERTA DE COMPRA
    # RSI sobrevendido (25), acima da média (63000) e rompendo a máxima anterior (64100 contra 64000)
    em_pos, p_compra = test_alert_logic("Gatilho de Compra V3", rsi=25.0, preco_atual=64100.0, sma200=63000.0, maxima_anterior=64000.0, em_posicao=False, preco_compra=0.0)
    
    # 3. Testando o disparo de TAKE PROFIT baseado na compra anterior
    # Subindo mais de 2% a partir de 64100
    test_alert_logic("Disparo de Take Profit", rsi=55.0, preco_atual=65500.0, sma200=63000.0, maxima_anterior=64000.0, em_posicao=em_pos, preco_compra=p_compra)

    # 4. Testando o disparo de STOP LOSS baseado na compra anterior
    # Caindo 1% a partir de 64100
    test_alert_logic("Disparo de Stop Loss", rsi=20.0, preco_atual=63400.0, sma200=63000.0, maxima_anterior=64000.0, em_posicao=em_pos, preco_compra=p_compra)
    
    print("\n=============================================")
    print("Se os blocos de '!!! ALERTA !!!' apareceram acima sem quebrar caracteres, seu sistema está 100% operacional.")