import sqlite3
from config import DB_NAME

def limpar_banco():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Opção 1: Limpar apenas o histórico de trades
        cursor.execute("DELETE FROM trade_history")
        
        # Opção 2: Resetar o estado do robô (para ele não achar que ainda está comprado)
        cursor.execute("DELETE FROM bot_state")
        
        # Opção 3: Limpar comandos pendentes
        cursor.execute("DELETE FROM commands")
        
        conn.commit()
        conn.close()
        print("✅ Banco de dados limpo com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao limpar o banco: {e}")

if __name__ == "__main__":
    confirmacao = input("Tem certeza que deseja apagar todos os dados de trades e estados? (s/n): ")
    if confirmacao.lower() == 's':
        limpar_banco()