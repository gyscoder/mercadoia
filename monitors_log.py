# monitor_logs.py
import time
print("--- ACOMPANHANDO DECISÕES DO ROBÔ ---")
with open("erros_sistema.txt", "r") as f:
    f.seek(0, 2) # Vai para o final do arquivo
    while True:
        line = f.readline()
        if line:
            print(line.strip())
        time.sleep(0.5)