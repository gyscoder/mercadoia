import sqlite3
from config import DB_NAME

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS commands (id INTEGER PRIMARY KEY AUTOINCREMENT, cmd TEXT)")
conn.commit()
conn.close()
print("Tabela 'commands' criada com sucesso!")