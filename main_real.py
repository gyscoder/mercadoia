#!/usr/bin/env python3
"""
Sistema de Trading REAL para MercadoIA MVP - Operando em REAIS (BRL)
IMPORTANTE: Este sistema opera com dinheiro real. Use com extrema cautela.
RECOMENDADO: Começar com valores muito baixos para teste.
CAPITAL INICIAL: 100 BRL (total da banca, não por trade)
"""

import time
import logging
from datetime import datetime
from config import WATCHLIST, TAKE_PROFIT_PCT, STOP_LOSS_PCT, INTERVALO_MONITORAMENTO, LOG_FILE
from data_engine import init_trading_tables, get_live_candles, load_state, save_state, log_trade, check_for_commands
from strategy import calcular_decisao
from detect_patterns_with_alerts import calculate_rsi
from exchange_api import BinanceAPI
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente (NUNCA commitar .env!)
load_dotenv()

# Configuração de logging seguro
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()  # Também exibe no console
    ]
)
logger = logging.getLogger(__name__)

class TradingReal:
    def __init__(self):
        """Inicializa o sistema de trading real com verificações de segurança"""
        self.exchange = None
        self.initialized = False
        self.emergency_stop = False

        # Configurações de risco (personalizáveis - valores em USDT)
        self.MAX_RISK_PER_TRADE = 0.02  # 2% do saldo USDT por trade
        self.MAX_DAILY_LOSS = 0.05      # 5% de perda diária máxima do saldo inicial

        # Estado do dia
        self.daily_start_balance = 0.0  # Em USDT

    def _usdt_to_brl_symbol(self, usdt_symbol):
        """
        Converte símbolo USDT para BRL (ex: BTCUSDT -> BTCBRL)
        Retorna None se o par BRL não existir
        """
        if not usdt_symbol.endswith('USDT'):
            return usdt_symbol  # Já não é USDT, retorna como está

        base_asset = usdt_symbol[:-4]  # Remove 'USDT'
        brl_symbol = base_asset + 'BRL'

        # Verifica se o par BRL existe na exchange
        try:
            self.exchange.get_symbol_info(brl_symbol)
            return brl_symbol
        except Exception:
            return None  # Par BRL não disponível

    def _get_brl_usdt_rate(self):
        """
        Obtém a taxa de conversão BRL/USDT (quanto 1 USDT vale em BRL)
        Levanta exceção se não conseguir obter a taxa
        """
        # Tenta obter o par USDTBRL (USDT em BRL)
        try:
            rate = self.exchange.get_ticker_price('USDTBRL')
            if rate:
                return float(rate)
        except Exception as e:
            logger.debug(f"Não foi possível obter USDTBRL: {e}")

        # Fallback: tenta calcular via BRLUSDT (1 BRL em USDT) e inverte
        try:
            rate = self.exchange.get_ticker_price('BRLUSDT')
            if rate:
                return 1.0 / float(rate)
        except Exception as e:
            logger.debug(f"Não foi possível obter BRLUSDT: {e}")

        # Se nenhuma das opções funcionar, levanta exceção
        raise RuntimeError("Não foi possível obter taxa de conversão BRL/USDT. Verifique conexão e pares disponíveis.")

    def initialize(self):
        """Inicializa conexão com exchange e verifica estado"""
        try:
            # Carrega credenciais de forma segura
            api_key = os.getenv('BINANCE_API_KEY')
            api_secret = os.getenv('BINANCE_API_SECRET')

            if not api_key or not api_secret:
                raise ValueError("Credenciais da Binance não encontradas. Defina BINANCE_API_KEY e BINANCE_API_SECRET no .env")

            # IMPORTANTE: Começar em testnet=True para testes iniciais!
            # Alterar para False apenas após testes extensivos
            self.exchange = BinanceAPI(api_key=api_key, api_secret=api_secret, testnet=False)

            # Testa conexão
            if not self.exchange.test_connection():
                raise ConnectionError("Falha ao conectar com a Binance API")

            # Obtém saldo inicial em BRL
            self.daily_start_balance = self.exchange.get_balance('BRL')
            logger.info(f"Sistema inicializado. Saldo inicial BRL: {self.daily_start_balance:.2f}")
            # Inicializa tabelas de trading (mantém separação com paper trading se necessário)
            init_trading_tables()

            self.initialized = True
            return True

        except Exception as e:
            logger.error(f"Falha na inicialização: {str(e)}")
            return False

    def check_risk_limits(self):
        """Verifica se está dentro dos limites de risco"""
        if not self.initialized:
            return False

        try:
            current_balance = self.exchange.get_balance('BRL')
            self.daily_pnl = current_balance - self.daily_start_balance

            # Verifica perda diária máxima (em BRL)
            max_daily_loss_brl = self.daily_start_balance * self.MAX_DAILY_LOSS
            if self.daily_pnl < (-max_daily_loss_brl):
                logger.warning(f"LIMITE DE PERDA DIÁRIA ATINGIDO: {self.daily_pnl:.2f} BRL (limite: {-max_daily_loss_brl:.2f} BRL)")
                return False

            # Verifica saldo mínimo para operar (pelo menos o valor mínimo da ordem)
            # Vamos verificar isso na criação da ordem específica
            return True

        except Exception as e:
            logger.error(f"Erro ao verificar limites de risco: {str(e)}")
            return False

    def calculate_position_size(self, symbol_usdt, entry_price_usdt):
        """
        Calcula o tamanho da posição baseado em gerenciamento de risco em USDT
        Retorna quantidade a ser tradada
        """
        try:
            # 1. Obter saldo disponível em USDT
            usdt_balance = self.exchange.get_balance('USDT')
            if usdt_balance <= 0:
                logger.warning(f"SALDO USDT INSUFICIENTE: {usdt_balance:.2f} USDT")
                return 0

            # 2. Calcular valor a arriscar (percentage do saldo USDT)
            risk_amount_usdt = usdt_balance * self.MAX_RISK_PER_TRADE
            logger.info(f"Saldo USDT disponível: {usdt_balance:.2f} | Valor a arriscar (2%): {risk_amount_usdt:.2f} USDT")

            # 3. Obter informações do símbolo para precisão e limites
            symbol_info = self.exchange.get_symbol_info(symbol_usdt)

            # 4. Encontrar filtros LOT_SIZE e MIN_NOTIONAL
            lot_size_step = 0.0
            min_notional = 0.0
            for f in symbol_info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    lot_size_step = float(f['stepSize'])
                elif f['filterType'] == 'MIN_NOTIONAL':
                    min_notional = float(f['notional'])

            logger.debug(f"Filtros para {symbol_usdt}: LOT_SIZE step={lot_size_step}, MIN_NOTIONAL={min_notional}")

            # 5. Calcular quantidade bruta baseado no risco
            raw_quantity = risk_amount_usdt / entry_price_usdt
            logger.debug(f"Quantidade bruta calculada: {raw_quantity:.8f}")

            # 6. Ajustar para o step size permitido
            if lot_size_step > 0:
                quantity = round(raw_quantity / lot_size_step) * lot_size_step
            else:
                quantity = raw_quantity

            # 7. Verificar quantidade mínima (LOT_SIZE minQty)
            min_qty = float([f['minQty'] for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'][0])
            if quantity < min_qty:
                logger.warning(f"Quantidade calculada ({quantity:.8f}) abaixo do mínimo permitido ({min_qty}). Ajustando para mínimo.")
                quantity = min_qty

            # 8. Verificar valor mínimo da ordem (MIN_NOTIONAL)
            order_value = quantity * entry_price_usdt
            if order_value < min_notional:
                logger.warning(f"Valor da ordem ({order_value:.2f} USDT) abaixo do MIN_NOTIONAL ({min_notional} USDT).")
                # Tentar ajustar para atingir MIN_NOTIONAL
                quantity_needed = min_notional / entry_price_usdt
                if lot_size_step > 0:
                    quantity = round(quantity_needed / lot_size_step) * lot_size_step
                else:
                    quantity = quantity_needed

                # Re-verificar após ajuste
                order_value = quantity * entry_price_usdt
                if order_value < min_notional:
                    logger.error(f"Não é possível criar ordem válida para {symbol_usdt}. Saldo disponível insuficiente.")
                    return 0
                else:
                    logger.info(f"Ordem ajustada para atender MIN_NOTIONAL: {quantity:.8f} (valor: {order_value:.2f} USDT)")

            # 9. Log final
            logger.info(f"Tamanho da posição calculado: {quantity:.8f} {symbol_usdt.split('USDT')[0]} (≈ {order_value:.2f} USDT em risco)")
            return quantity

        except Exception as e:
            logger.error(f"Erro ao calcular tamanho da posição: {str(e)}")
            return 0

    def execute_trade(self, symbol, side, quantity, order_type='MARKET'):
        """
        Executa uma ordem real na exchange
        """
        try:
            if not self.exchange:
                raise RuntimeError("Exchange não inicializada")

            logger.info(f"EXECUTANDO ORDEM: {side} {quantity:.8f} {symbol} ({order_type})")

            # Para ordens de mercado, obtemos preço atual para logging
            if order_type == 'MARKET':
                price_before = self.exchange.get_ticker_price(symbol)
            else:
                price_before = None

            # Envia a ordem
            order_response = self.exchange.create_order(
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity
            )

            # Processa resposta
            if order_response and order_response.get('status') == 'FILLED':
                # Ordem totalmente preenchida
                filled_qty = float(order_response['executedQty'])
                avg_price = float(order_response['avgPrice']) if order_response['avgPrice'] > 0 else \
                           float(order_response['fills'][0]['price']) if order_response.get('fills') else 0

                logger.info(f"ORDEM EXECUTADA: {side} {filled_qty:.8f} {symbol} @ {avg_price:.4f}")

                # Registra no sistema de logging interno (para estratégia)
                if side == 'BUY':
                    # Para compra, salvamos apenas o preço de entrada (quantidade será obtida da exchange na venda)
                    save_state(symbol, True, avg_price)
                    log_trade(symbol, "COMPRA_REAL", avg_price, 0, 0)  # P&L será atualizado na venda
                else:
                    # Para venda, precisamos do preço de entrada
                    _, entry_price = load_state(symbol)
                    if entry_price > 0:
                        pct = ((avg_price - entry_price) / entry_price) * 100
                        log_trade(symbol, "VENDA_REAL", entry_price, avg_price, pct)
                        save_state(symbol, False, 0.0)  # Zerar posição
                    else:
                        logger.warning(f"Não foi possível calcular P&L para {symbol}: entrada não encontrada")

                return True, order_response
            else:
                logger.error(f"Ordem não foi preenchida: {order_response}")
                return False, order_response

        except Exception as e:
            logger.error(f"Erro ao executar ordem: {str(e)}")
            return False, None

    def manage_position(self, symbol):
        """
        Gerencia uma posição aberta (verifica stop loss, take profit, etc.)
        Nota: Esta versão simples usa ordens de mercado. Em produção,
        seria melhor usar ordens de limite/stop separadas.
        """
        try:
            em_posicao, preco_entrada = load_state(symbol)
            if not em_posicao or preco_entrada <= 0:
                return  # Nenhuma posição para gerenciar

            preco_atual = self.exchange.get_ticker_price(symbol)
            if not preco_atual:
                return

            # Calcula variação
            variacao = (preco_atual - preco_entrada) / preco_entrada

            # Lógica simplificada de gestão (igual à strategy.py por enquanto)
            # Em produção, separaríamos ordens de limite/stop separadas
            if variacao <= -STOP_LOSS_PCT:
                 logger.info(f"STOP LOSS ATINGIDO para {symbol}: {variacao*100:.2f}%")
                 # Obter quantidade da posição atual (para pares USDT)
                 base_asset = symbol.replace('USDT', '')
                 quantidade = self.exchange.get_balance(base_asset)
                 if quantidade > 0:
                     self.execute_trade(symbol, 'SELL', quantidade)
            elif variacao >= TAKE_PROFIT_PCT:
                 logger.info(f"TAKE PROFIT ATINGIDO para {symbol}: {variacao*100:.2f}%")
                 base_asset = symbol.replace('USDT', '')
                 quantidade = self.exchange.get_balance(base_asset)
                 if quantidade > 0:
                     self.execute_trade(symbol, 'SELL', quantidade)

        except Exception as e:
            logger.error(f"Erro ao gerenciar posição para {symbol}: {str(e)}")

    def run(self):
        """Loop principal de trading"""
        if not self.initialize():
            logger.error("Falha ao inicializar sistema. Abortando.")
            return

        logger.info("=== INICIANDO SISTEMA DE TRADING REAL (BRL) ===")
        logger.warning("ATENÇÃO: Este sistema está operando com DINHEIRO REAL EM REAIS!")
        logger.info(f"Capital inicial (banca): {self.daily_start_balance:.2f} BRL")
        logger.info(f"Risco máximo por trade: {self.MAX_RISK_PER_TRADE*100}% da banca")
        logger.info(f"Perda diária máxima: {self.MAX_DAILY_LOSS*100}% da banca inicial")

        try:
            while not self.emergency_stop:
                # Verifica comandos do GUI (PAUSAR, RESUMIR, VENDA_TOTAL)
                comando = check_for_commands()
                if comando == "PAUSAR":
                    logger.info("SISTEMA PAUSADO pelo GUI. Aguardando RESUMIR...")
                    while True:
                        time.sleep(5)
                        if check_for_commands() == "RESUMIR":
                            logger.info("SISTEMA RESUMIDO pelo GUI.")
                            break
                        elif check_for_commands() == "VENDA_TOTAL":
                            comando = "VENDA_TOTAL"
                            break

                if comando == "VENDA_TOTAL":
                      logger.warning("!!! COMANDO DE VENDA TOTAL RECEBIDO !!!")
                      # Lógica para vender todas as posições
                      for symbol in WATCHLIST:
                          # Para pares USDT, usamos o símbolo diretamente
                          usdt_symbol = self._usdt_symbol(symbol)  # Garante que seja XXXUSDT

                          em_posicao, _ = load_state(symbol)  # Verifica posição usando símbolo original
                          if em_posicao:
                              base_asset = usdt_symbol.replace('USDT', '')
                              quantidade = self.exchange.get_balance(base_asset)
                              if quantidade > 0:
                                  self.execute_trade(usdt_symbol, 'SELL', quantidade)
                      break  # Sai do loop após venda total

                # Verifica limites de risco antes de operar
                if not self.check_risk_limits():
                    logger.warning("Limites de risco excedidos. Aguardando próximo ciclo...")
                    time.sleep(INTERVALO_MONITORAMENTO)
                    continue

                # Processa cada símbolo na watchlist (ou apenas o símbolo especificado)
                symbols_to_process = [self.symbol_override] if hasattr(self, 'symbol_override') and self.symbol_override else WATCHLIST
                for symbol in symbols_to_process:
                    if self.emergency_stop:
                        break

                    try:
                        # Pula se houver pausa ativa (já tratado acima, mas dupla verificação)
                        if check_for_commands() == "PAUSAR":
                            continue

                        # Converte para símbolo BRL para trading
                        brl_symbol = self._usdt_to_brl_symbol(symbol)
                        if brl_symbol is None:
                            logger.warning(f"Par BRL não disponível para {symbol}, pulando análise...")
                            continue

                        # Busca dados de mercado (usamos o par USDT original para análise, pois geralmente tem melhor liquidez/dados)
                        klines = get_live_candles(symbol)  # Usa o símbolo original (USDT) para análise
                        if not klines or len(klines) < 200:  # Necessário para SMA200
                            logger.warning(f"Dados insuficientes para {symbol} (análise em {symbol})")
                            continue

                        # Calcula indicadores (igual ao main.py)
                        closes = [float(k[4]) for k in klines]
                        volumes = [float(k[5]) for k in klines]
                        preco_atual_usdt = closes[-1]
                        sma200 = sum(closes[-200:]) / 200 if len(closes) >= 200 else None
                        rsi = calculate_rsi(closes)

                        if sma200 is None:
                            continue

                        # Lógica de decisão (igual à strategy.py)
                        volume_atual = volumes[-1]
                        media_volume = sum(volumes[-21:-1]) / 20 if len(volumes) >= 21 else 0

                        # Importamos VOL_MULTIPLIER do config
                        from config import VOL_MULTIPLIER
                        filtro_volume = volume_atual > (media_volume * VOL_MULTIPLIER)
                        filtro_rsi = rsi < 70

                        em_posicao, preco_compra = load_state(symbol)  # Usa símbolo original para consistência com data_engine

                        # Log formatado (mostramos preço em USDT para consistência com análise do paper trading)
                        status_pos = "$$ COMPRADO (Gerenciando...)" if em_posicao else ".::|BUSCANDO|::."
                        logger.info(
                            f"{symbol.ljust(9)} | P: {preco_atual_usdt:<8,.2f} (USDT) | "
                            f"SMA200: {sma200:<8,.2f} (USDT) | RSI: {rsi:<5.2f} | "
                            f"Vol: {int(volume_atual)} | Status: {status_pos}"
                        )

                        # Converte preço para BRL usando taxa atual
                        try:
                            brl_usdt_rate = self._get_brl_usdt_rate()
                            preco_atual_brl = preco_atual_usdt * brl_usdt_rate
                            sma200_brl = sma200 * brl_usdt_rate if sma200 else None
                        except Exception as e:
                            logger.error(f"Falha ao obter taxa de conversão BRL/USDT: {e}")
                            continue  # Pula este ciclo se não puder converter

                        # Calcula decisão baseada na análise (os indicadores são proporcionais, então podemos usar os valores USDT diretamente)
                        # RSI e comparações de preço são independentes da moeda de cotação
                        comando_trade, resultado = calcular_decisao(
                            preco_atual_usdt, sma200, volume_atual, media_volume,
                            em_posicao, preco_compra, rsi, TAKE_PROFIT_PCT, STOP_LOSS_PCT
                        )

                        # Executa ações baseado na decisão (usando o par BRL para trading)
                        if comando_trade == "COMPRA" and not em_posicao:
                            # Verifica se já temos posição (dupla verificação)
                            em_posicao_check, _ = load_state(symbol)
                            if not em_posicao_check:
                                # Calcula tamanho da posição em BRL
                                quantidade = self.calculate_position_size(brl_symbol, preco_atual_brl)
                                if quantidade > 0:
                                    success, _ = self.execute_trade(brl_symbol, 'BUY', quantidade)
                                    if success:
                                        logger.info(f"COMPRA EXECUTADA para {symbol} (via {brl_symbol})")
                                    else:
                                        logger.error(f"FALHA NA COMPRA para {symbol} (via {brl_symbol})")

                        elif comando_trade == "VENDA" and em_posicao:
                            # Gestão de posição (stop loss, take profit)
                            self.manage_position(brl_symbol)

                        # Pequena pausa entre símbolos para não sobrecarregar API
                        time.sleep(0.5)

                    except Exception as e:
                        logger.error(f"Erro ao processar {symbol}: {str(e)}")
                        continue

                # Intervalo entre varreduras completas
                time.sleep(INTERVALO_MONITORAMENTO)

        except KeyboardInterrupt:
            logger.info("Sistema interrompido pelo usuário")
        except Exception as e:
            logger.error(f"Erro crítico no loop principal: {str(e)}")
        finally:
            logger.info("=== SISTEMA DE TRADING REAL ENCERRADO ===")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='MercadoIA Trading Bot')
    parser.add_argument('--symbol', type=str, help='Symbol to trade (e.g., SOLUSDT). Overrides watchlist.')
    args = parser.parse_args()

    trader = TradingReal()
    # If a symbol is provided via command line, temporarily override the watchlist
    if args.symbol:
        # We'll store it in the trader instance to use in run() method
        trader.symbol_override = args.symbol.upper()
    else:
        trader.symbol_override = None
    trader.run()