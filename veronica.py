#!/usr/bin/env python3
"""
Sistema de Trading REAL para MercadoIA - Estrutura Completa
Uso no Windows: python main_real.py --base USDT --symbols BTCUSDT SOLUSDT
"""

import time
import logging
import argparse
import os
from dotenv import load_dotenv

# Importações dos seus módulos originais
from config import TAKE_PROFIT_PCT, STOP_LOSS_PCT, INTERVALO_MONITORAMENTO, LOG_FILE
from data_engine import init_trading_tables, get_live_candles, load_state, save_state, log_trade, check_for_commands
from strategy import calcular_decisao
from detect_patterns_with_alerts import calculate_rsi
from exchange_api import BinanceAPI

load_dotenv()

# Configuração de logging adaptada para Windows (caminhos e codificação)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TradingReal:
    def __init__(self, base_currency, symbols):
        self.base_currency = base_currency  # ex: USDT
        self.symbols = symbols              # ex: ['BTCUSDT', 'SOLUSDT']
        self.exchange = None
        self.initialized = False
        self.emergency_stop = False
        
        # Parâmetros de Risco
        self.MAX_RISK_PER_TRADE = 0.02
        self.MAX_DAILY_LOSS = 0.05
        self.daily_start_balance = 0.0

    def initialize(self):
        try:
            api_key = os.getenv('BINANCE_API_KEY')
            api_secret = os.getenv('BINANCE_API_SECRET')
            if not api_key or not api_secret:
                raise ValueError("Credenciais não encontradas no .env")

            self.exchange = BinanceAPI(api_key=api_key, api_secret=api_secret, testnet=False)
            if not self.exchange.test_connection():
                raise ConnectionError("Falha ao conectar na Binance")

            self.daily_start_balance = self.exchange.get_balance(self.base_currency)
            logger.info(f"Sistema inicializado. Saldo inicial em {self.base_currency}: {self.daily_start_balance:.2f}")
            
            init_trading_tables()
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Erro na inicialização: {e}")
            return False

    def check_risk_limits(self):
        try:
            current_balance = self.exchange.get_balance(self.base_currency)
            self.daily_pnl = current_balance - self.daily_start_balance
            if self.daily_pnl < -(self.daily_start_balance * self.MAX_DAILY_LOSS):
                logger.warning("Limite de perda diária atingido!")
                return False
            return True
        except Exception as e:
            logger.error(f"Erro ao verificar riscos: {e}")
            return False

    def execute_trade(self, symbol, side, quantity):
        try:
            response = self.exchange.create_order(symbol=symbol, side=side, type='MARKET', quantity=quantity)
            if response and response.get('status') == 'FILLED':
                avg_price = float(response.get('avgPrice', 0))
                if side == 'BUY':
                    save_state(symbol, True, avg_price)
                    log_trade(symbol, "COMPRA_REAL", avg_price, 0, 0)
                else:
                    save_state(symbol, False, 0.0)
                return True
            return False
        except Exception as e:
            logger.error(f"Erro na execução da ordem: {e}")
            return False

    def run(self):
        if not self.initialize(): return

        while not self.emergency_stop:
            comando = check_for_commands()
            if comando == "PAUSAR":
                time.sleep(5)
                continue
            
            if not self.check_risk_limits():
                time.sleep(INTERVALO_MONITORAMENTO)
                continue

            for symbol in self.symbols:
                klines = get_live_candles(symbol)
                if not klines or len(klines) < 200: continue
                
                closes = [float(k[4]) for k in klines]
                price = closes[-1]
                sma200 = sum(closes[-200:]) / 200
                rsi = calculate_rsi(closes)
                
                em_posicao, preco_entrada = load_state(symbol)
                
                # Executa estratégia
                decisao, _ = calcular_decisao(price, sma200, 0, 0, em_posicao, preco_entrada, rsi, TAKE_PROFIT_PCT, STOP_LOSS_PCT)
                
                if decisao == "COMPRA" and not em_posicao:
                    balance = self.exchange.get_balance(self.base_currency)
                    qty = (balance * self.MAX_RISK_PER_TRADE) / price
                    self.execute_trade(symbol, 'BUY', qty)
                
                elif decisao == "VENDA" and em_posicao:
                    asset = symbol.replace(self.base_currency, '')
                    qty = self.exchange.get_balance(asset)
                    self.execute_trade(symbol, 'SELL', qty)

            time.sleep(INTERVALO_MONITORAMENTO)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Trading Bot Real')
    parser.add_argument('--base', required=True, help='Moeda base ex: USDT')
    parser.add_argument('--symbols', nargs='+', required=True, help='Pares ex: BTCUSDT SOLUSDT')
    args = parser.parse_args()

    trader = TradingReal(args.base.upper(), [s.upper() for s in args.symbols])
    trader.run()