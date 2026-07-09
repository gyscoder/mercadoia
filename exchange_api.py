#!/usr/bin/env python3
"""
Módulo seguro para interação com APIs de exchanges (Binance foco)
Projeto: MercadoIA MVP - Trading Real
"""

import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode
import logging
from config import LOG_FILE

class BinanceAPI:
    """
    Cliente seguro para API da Binance com:
    - Assinatura HMAC-SHA256
    - Tratamento de erros e rate limits
    - Suporte a testnet e live
    - Logging seguro (sem credenciais)
    """

    def __init__(self, api_key=None, api_secret=None, testnet=True):
        """
        Inicializa o cliente da API

        Args:
            api_key (str): API Key da Binance (opcional se variáveis de ambiente)
            api_secret (str): API Secret da Binance (opcional se variáveis de ambiente)
            testnet (bool): Usar testnet da Binance (padrão: True para segurança)
        """
        # Prioridade: parâmetros > variáveis de ambiente > erro
        import os
        from dotenv import load_dotenv
        load_dotenv()  # Carrega .env se existir

        self.api_key = api_key or os.getenv('BINANCE_API_KEY')
        self.api_secret = api_secret or os.getenv('BINANCE_API_SECRET')

        if not self.api_key or not self.api_secret:
            raise ValueError(
                "API Key e Secret são obrigatórios. "
                "Defina como parâmetros ou variáveis de ambiente BINANCE_API_KEY/BINANCE_API_SECRET"
            )

        self.testnet = testnet
        self.base_url = "https://testnet.binance.vision" if testnet else "https://api.binance.com"
        self.recv_window = 5000  # Janela de timestamp válida (ms)

        # Configurar logging seguro (nunca loga credenciais)
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:  # Evita duplicação de handlers
            handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _get_timestamp(self):
        """Retorna timestamp em milissegundos"""
        return int(time.time() * 1000)

    def _sign_request(self, params):
        """
        Cria assinatura HMAC-SHA256 para os parâmetros

        Args:
            params (dict): Parâmetros da requisição

        Returns:
            str: Assinatura hexadecimal
        """
        query_string = urlencode(params, doseq=True)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _send_request(self, http_method, endpoint, params=None, signed=False):
        """
        Envia requisição para a API da Binance

        Args:
            http_method (str): GET, POST, DELETE, etc.
            endpoint (str): Endpoint da API (ex: '/api/v3/account')
            params (dict): Parâmetros da requisição
            signed (bool): Se a requisição precisa de assinatura

        Returns:
            dict: Resposta JSON da API

        Raises:
            Exception: Para erros de API ou conexão
        """
        if params is None:
            params = {}

        # Adiciona timestamp obrigatório para requisições assinadas
        if signed:
            params['timestamp'] = self._get_timestamp()
            # Adjanela de recvWindow para evitar problemas de sincronização de tempo
            params['recvWindow'] = self.recv_window

        # Cria assinatura se necessário
        if signed:
            params['signature'] = self._sign_request(params)

        # Headers necessários
        headers = {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        url = f"{self.base_url}{endpoint}"

        try:
            if http_method.upper() == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=10)
            elif http_method.upper() == 'POST':
                response = requests.post(url, data=params, headers=headers, timeout=10)
            elif http_method.upper() == 'DELETE':
                response = requests.delete(url, params=params, headers=headers, timeout=10)
            else:
                raise ValueError(f"Método HTTP não suportado: {http_method}")

            # Tratamento de rate limits e outros erros HTTP
            if response.status_code == 429:
                self.logger.warning("Rate limit atingido. Aguardando 60 segundos...")
                time.sleep(60)
                # Retry após espera
                return self._send_request(http_method, endpoint, params, signed)

            response.raise_for_status()  # Levanta exceção para 4xx/5xx
            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro na requisição para {endpoint}: {str(e)}")
            # Não levanta exceção imediatamente para permitir tratamento específico no caller
            raise ConnectionError(f"Falha na conexão com Binance API: {str(e)}")
        except ValueError as e:  # Erro JSON
            self.logger.error(f"Resposta inválida da API: {response.text}")
            raise ValueError(f"Resposta inválida da Binance API: {response.text}")

    # ===== MÉTODOS PÚBLICOS =====

    def test_connection(self):
        """
        Testa conectividade com a API e validade das credenciais

        Returns:
            bool: True se conexão OK e credenciais válidas
        """
        try:
            # Endpoint público não requer autenticação
            ping = self._send_request('GET', '/api/v3/ping', signed=False)
            # Endpoint de conta requer autenticação
            account = self._send_request('GET', '/api/v3/account', signed=True)
            self.logger.info("Conexão com Binance API estabelecida com sucesso")
            return True
        except Exception as e:
            self.logger.error(f"Falha ao testar conexão: {str(e)}")
            return False

    def get_account_info(self):
        """
        Obtém informações da conta (saldo, permissões, etc.)

        Returns:
            dict: Informações da conta
        """
        return self._send_request('GET', '/api/v3/account', signed=True)

    def get_balance(self, asset):
        """
        Obtém saldo livre de um ativo específico

        Args:
            asset (str): Símbolo do ativo (ex: 'USDT', 'BTC')

        Returns:
            float: Saldo livre disponível
        """
        account_info = self.get_account_info()
        for balance in account_info['balances']:
            if balance['asset'] == asset:
                return float(balance['free'])
        return 0.0

    def get_symbol_info(self, symbol):
        """
        Obtém informações de um símbolo (precisão, limites, etc.)

        Args:
            symbol (str): Par de trading (ex: 'BTCUSDT')

        Returns:
            dict: Informações do símbolo
        """
        exchange_info = self._send_request('GET', '/api/v3/exchangeInfo', signed=False)
        for s in exchange_info['symbols']:
            if s['symbol'] == symbol:
                return s
        raise ValueError(f"Símbolo {symbol} não encontrado na exchange")

    def get_ticker_price(self, symbol):
        """
        Obtém preço atual do ticker

        Args:
            symbol (str): Par de trading (ex: 'BTCUSDT')

        Returns:
            float: Preço atual
        """
        ticker = self._send_request('GET', '/api/v3/ticker/price',
                                  params={'symbol': symbol}, signed=False)
        return float(ticker['price'])

    def get_klines(self, symbol, interval='1m', limit=500):
        """
        Obtém dados de candlesticks (klines)

        Args:
            symbol (str): Par de trading
            interval (str): Intervalo (1m, 5m, 1h, 1d, etc.)
            limit (int): Número de klines (máx 1000)

        Returns:
            list: Lista de klines no formato [timestamp, open, high, low, close, volume, ...]
        """
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        return self._send_request('GET', '/api/v3/klines', params=params, signed=False)

    def create_order(self, symbol, side, type, quantity, price=None,
                    timeInForce='GTC', stopPrice=None, icebergQty=None):
        """
        Cria uma nova ordem na exchange

        Args:
            symbol (str): Par de trading (ex: 'BTCUSDT')
            side (str): 'BUY' ou 'SELL'
            type (str): Tipo de ordem ('LIMIT', 'MARKET', 'STOP_LOSS_LIMIT', etc.)
            quantity (float): Quantidade a ser tradada
            price (float, opcional): Preço (obrigatório para LIMIT)
            timeInForce (str): 'GTC', 'IOC', 'FOK' (padrão: 'GTC')
            stopPrice (float, opcional): Preço de gatilho para stop orders
            icebergQty (float, opcional): Para ordens iceberg

        Returns:
            dict: Resposta da ordem criada

        Raises:
            ValueError: Para parâmetros inválidos
        """
        # Validações básicas
        if side not in ['BUY', 'SELL']:
            raise ValueError("Side deve ser 'BUY' ou 'SELL'")

        if type == 'LIMIT' and price is None:
            raise ValueError("Preço é obrigatório para ordens LIMIT")

        params = {
            'symbol': symbol,
            'side': side,
            'type': type,
            'quantity': quantity,
        }

        if price is not None:
            params['price'] = price
        if timeInForce:
            params['timeInForce'] = timeInForce
        if stopPrice is not None:
            params['stopPrice'] = stopPrice
        if icebergQty is not None:
            params['icebergQty'] = icebergQty

        self.logger.info(f"Enviando ordem: {side} {quantity} {symbol} @ {type}")
        return self._send_request('POST', '/api/v3/order', params=params, signed=True)

    def cancel_order(self, symbol, orderId):
        """
        Cancela uma ordem aberta

        Args:
            symbol (str): Par de trading
            orderId (int): ID da ordem a ser cancelada

        Returns:
            dict: Confirmação do cancelamento
        """
        params = {
            'symbol': symbol,
            'orderId': orderId
        }
        return self._send_request('DELETE', '/api/v3/order', params=params, signed=True)

    def get_open_orders(self, symbol=None):
        """
        Obtém ordens abertas

        Args:
            symbol (str, opcional): Filtrar por símbolo

        Returns:
            list: Lista de ordens abertas
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._send_request('GET', '/api/v3/openOrders', params=params, signed=True)

    def get_order(self, symbol, orderId):
        """
        Obtém detalhes de uma ordem específica

        Args:
            symbol (str): Par de trading
            orderId (int): ID da ordem

        Returns:
            dict: Detalhes da ordem
        """
        params = {
            'symbol': symbol,
            'orderId': orderId
        }
        return self._send_request('GET', '/api/v3/order', params=params, signed=True)

# Exemplo de uso seguro (NUNCA commitar com credenciais reais!)
if __name__ == "__main__":
    # Este bloco é apenas para demonstração - NÃO usar em produção sem .env
    print("Para usar, defina BINANCE_API_KEY e BINANCE_API_SECRET em variáveis de ambiente ou .env")
    print("Exemplo de .env:")
    print("BINANCE_API_KEY=sua_chave_aqui")
    print("BINANCE_API_SECRET=seu_segredo_aqui")
    print("\nPara testnet (recomendado para início):")
    print("api = BinanceAPI(testnet=True)")
    print("\nPara live trading (após testes extensivos):")
    print("api = BinanceAPI(testnet=False)")