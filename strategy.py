from detect_patterns_with_alerts import calculate_rsi
from config import VOL_MULTIPLIER # Importamos o multiplicador aqui

def calculate_sma(prices, period=200):
    return sum(prices[-period:]) / period if len(prices) >= period else None

def calcular_decisao(preco_atual, sma200, volume_atual, media_volume, em_posicao, preco_compra, rsi, TAKE_PROFIT_PCT, STOP_LOSS_PCT):
    filtro_volume = volume_atual > (media_volume * VOL_MULTIPLIER)
    filtro_rsi = rsi < 70 

    if em_posicao:
        # --- Lógica de Venda (Trailing/Take/Stop) ---
        variacao = (preco_atual - preco_compra) / preco_compra
        
        # Define o stop dinâmico (protege lucro após 1% de ganho)
        stop_dinamico = preco_compra if variacao < 0.01 else (preco_atual * 0.995)
        
        # Gatilhos de Venda
        if preco_atual <= stop_dinamico and variacao > 0.005: 
            return "VENDA", ("TRAILING_STOP", variacao*100)
        if variacao >= TAKE_PROFIT_PCT: 
            return "VENDA", ("TAKE_PROFIT", variacao*100)
        if variacao <= -STOP_LOSS_PCT: 
            return "VENDA", ("STOP_LOSS", variacao*100)
            
        # Se não vendeu, podemos tentar o ajuste de stop (opcional)
        if preco_atual > preco_compra * 1.05:
            return "AJUSTAR_STOP", preco_atual * 0.98
            
        return "MANTER", None

    else:
        # --- Lógica de Compra ---
        if preco_atual > sma200 and filtro_volume and filtro_rsi:
            return "COMPRA", preco_atual
        return "AGUARDAR", None