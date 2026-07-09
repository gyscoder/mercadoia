from exchange_api import BinanceAPI
import os
from dotenv import load_dotenv

load_dotenv()

def test_system():
    print("Iniciando bateria de testes na Binance...")
    api = BinanceAPI(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'), testnet=True)
    
    # Teste 1: Conexão
    if api.test_connection():
        print("✅ Conexão OK")
    else:
        print("❌ Falha na conexão")
        return

    # Teste 2: Saldo BRL
    saldo = api.get_balance('BRL')
    print(f"💰 Saldo BRL: {saldo}")
    
    # Teste 3: Ticker (Preço)
    preco = api.get_ticker_price('BTCBRL')
    print(f"📊 Preço BTCBRL: {preco}")

if __name__ == "__main__":
    test_system()