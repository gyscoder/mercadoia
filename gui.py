import tkinter as tk
from tkinter import ttk
import subprocess
import sqlite3
import os
import threading
import time
from datetime import datetime
from config import DB_NAME
from subprocess import CREATE_NEW_CONSOLE

# Variável global para armazenar o processo do robô
processo_robo = None
processo_monitor = None
processo_relatorio = None

# Cores do tema futurista profissional
COLORS = {
    'bg_primary': '#0a0f1c',      # Azul marinho muito escuro
    'bg_secondary': '#111827',    # Azul escuro
    'bg_tertiary': '#1e293b',     # Azul cinza
    'accent_cyan': '#00f5ff',     # Ciano vibrante
    'accent_purple': '#8b5cf6',   # Roxo moderno
    'accent_green': '#10b981',    # Verde esmeralda
    'accent_red': '#ef4444',      # Vermelho suave
    'text_primary': '#f8fafc',    # Branco quase puro
    'text_secondary': '#94a3b8',  # Cinza claro
    'text_muted': '#64748b',      # Cinza médio
    'border': '#334155',          # Borda sutil
    'success': '#10b981',
    'warning': '#f59e0b',
    'error': '#ef4444'
}

def aplicar_tema_futurista(root):
    """Aplica um tema moderno e futurista à interface"""
    style = ttk.Style()

    # Configurar tema base
    style.theme_use('clam')

    # Configurar cores e estilos
    style.configure('.',
                   background=COLORS['bg_primary'],
                   foreground=COLORS['text_primary'],
                   font=('Segoe UI', 9))

    style.configure('TFrame',
                   background=COLORS['bg_primary'])

    style.configure('TLabel',
                   background=COLORS['bg_primary'],
                   foreground=COLORS['text_primary'],
                   font=('Segoe UI', 9))

    style.configure('TLabelFrame',
                   background=COLORS['bg_primary'],
                   foreground=COLORS['text_primary'],
                   borderwidth=1,
                   relief='solid')

    style.configure('TLabelFrame.Label',
                   background=COLORS['bg_primary'],
                   foreground=COLORS['accent_cyan'],
                   font=('Segoe UI', 10, 'bold'))

    style.configure('TNotebook',
                   background=COLORS['bg_primary'],
                   borderwidth=0)

    style.configure('TNotebook.Tab',
                   background=COLORS['bg_secondary'],
                   foreground=COLORS['text_secondary'],
                   padding=[12, 8],
                   font=('Segoe UI', 9, 'bold'))

    style.map('TNotebook.Tab',
             background=[('selected', COLORS['bg_tertiary']),
                        ('active', COLORS['bg_tertiary'])],
             foreground=[('selected', COLORS['accent_cyan']),
                        ('active', COLORS['accent_cyan'])])

    style.configure('TButton',
                   background=COLORS['bg_tertiary'],
                   foreground=COLORS['text_primary'],
                   borderwidth=1,
                   focuscolor='none',
                   padding=[10, 6],
                   font=('Segoe UI', 9))

    style.map('TButton',
             background=[('active', COLORS['accent_cyan']),
                        ('pressed', COLORS['accent_purple'])],
             foreground=[('active', COLORS['bg_primary']),
                        ('pressed', COLORS['text_primary'])])

    # Estilos especiais para botões de ação
    style.configure('Accent.TButton',
                   background=COLORS['accent_cyan'],
                   foreground=COLORS['bg_primary'],
                   font=('Segoe UI', 9, 'bold'))

    style.map('Accent.TButton',
             background=[('active', '#33cfff'),
                        ('pressed', '#00b5d4')])

    style.configure('Success.TButton',
                   background=COLORS['accent_green'],
                   foreground=COLORS['bg_primary'])

    style.map('Success.TButton',
             background=[('active', '#059669'),
                        ('pressed', '#047857')])

    style.configure('Danger.TButton',
                   background=COLORS['accent_red'],
                   foreground=COLORS['bg_primary'])

    style.map('Danger.TButton',
             background=[('active', '#dc2626'),
                        ('pressed', '#b91c1c')])

def abrir_script(nome_script):
    """Abre um script em uma nova janela de terminal"""
    try:
        # Abre o script em uma nova janela de terminal, igual ao robô
        subprocess.Popen(["python", nome_script], creationflags=subprocess.CREATE_NEW_CONSOLE)
        print(f"Abrindo {nome_script}...")
        return True
    except Exception as e:
        print(f"Erro ao abrir {nome_script}: {e}")
        return False

def iniciar_robo(status_label, btn_iniciar, btn_parar):
    """Inicia o robô de trading"""
    global processo_robo

    # Verifique se o arquivo main_real.py existe antes de tentar iniciar
    if not os.path.exists("main_real.py"):
        status_label.config(text="❌ ERRO: Arquivo main_real.py não encontrado",
                          foreground=COLORS['accent_red'])
        return

    # Só inicia se o processo não existir ou já tiver finalizado
    if processo_robo is None or processo_robo.poll() is not None:
        try:
            # Esta linha abre o main_real.py em sua própria janela de console (Windows)
            processo_robo = subprocess.Popen(
                ["python", "main_real.py"],
                creationflags=CREATE_NEW_CONSOLE # <-- CORREÇÃO AQUI
            )
            status_label.config(text=f"🟢 ROBÔ ATIVO (PID: {processo_robo.pid})",
                              foreground=COLORS['accent_green'])
            btn_iniciar.config(state='disabled')
            btn_parar.config(state='normal')
            print(f"Robô iniciado com PID: {processo_robo.pid}")
        except Exception as e:
            status_label.config(text=f"❌ ERRO AO INICIAR: {str(e)}",
                              foreground=COLORS['accent_red'])
            print(f"Erro ao iniciar o robô: {e}")
    else:
        status_label.config(text="⚠️ ROBÔ JÁ ESTÁ EM EXECUÇÃO",
                          foreground=COLORS['accent_red'])

def parar_robo(status_label, btn_iniciar, btn_parar):
    """Para o robô de trading"""
    global processo_robo
    if processo_robo is not None:
        try:
            processo_robo.terminate()
            processo_robo = None
            status_label.config(text="🔴 ROBÔ PARADO",
                              foreground=COLORS['accent_red'])
            btn_iniciar.config(state='normal')
            btn_parar.config(state='disabled')
            print("Robô parado.")
        except Exception as e:
            status_label.config(text=f"❌ ERRO AO PARAR: {str(e)}",
                              foreground=COLORS['accent_red'])
            print(f"Erro ao parar o robô: {e}")

def enviar_comando(cmd):
    """Envia um comando para o robô via banco de dados"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO commands (cmd) VALUES (?)", (cmd,))
        conn.commit()
        conn.close()
        print(f"Comando enviado: {cmd}")
        return True
    except Exception as e:
        print(f"Erro ao enviar comando: {e}")
        return False

def mostrar_ajuda():
    """Exibe uma janela de ajuda com informações sobre o sistema"""
    ajuda_texto = """MERCADOIA PRO - SISTEMA DE TRADING
========================================

FUNÇÕES DISPONÍVEIS:

1. CONTROLE DO ROBÔ:
   • INICIAR ROBÔ: Inicia o sistema de trading em modo real (USDT)
   • PARAR ROBÔ: Para a execução do robô de trading
   • EMERGÊNCIA: VENDER TUDO: Vende imediatamente todas as posições abertas
   • PAUSAR: Temporariamente suspende novas operações
   • RETOMAR: Restaura as operações após pausa

2. ANÁLISE E MONITORAMENTO:
   • VER LOGS DETALHADOS: Abre o monitor de logs em tempo real
   • SALVAR LOGS: Exporta o histórico de logs para arquivo
   • LIMPAR LOGS: Limpa a visualização de logs na interface

3. RELATÓRIOS:
   • GERAR RELATÓRIO: Cria relatório de desempenho do sistema
   • EXPORTAR DADOS: Exporta dados históricos de trading

4. LINHA DE COMANDO (AVANÇADO):
   Para especificar um par de trading específico, use:
   python main_real.py --symbol SYMBOL

   Exemplo: python main_real.py --symbol SOLUSDT

   Se nenhum símbolo for especificado, o sistema usa a watchlist do config.py

5. CONFIGURAÇÃO DE RISCO:
   • Risco por trade: 2% do saldo disponível
   • Perda diária máxima: 5% do saldo inicial
   • Saldo em USDT usado para cálculos de posição

OBSERVAÇÕES IMPORTANTES:
• Este sistema opera com DINHEIRO REAL - use com extrema cautela
• Sempre comece com valores baixos para teste
• Monitore os logs continuamente durante as operações
• O saldo USDT é atualizado em tempo real na interface
• Use a faucet da Binance testnet para testes sem risco (altere testnet=True em main_real.py)

© 2026 MercadoIA Pro - Sistema de Trading Profesional
"""

    # Cria uma janela de ajuda
    ajuda_window = tk.Toplevel()
    ajuda_window.title("❓ Ajuda - MercadoIA Pro")
    ajuda_window.geometry("600x500")
    ajuda_window.configure(bg=COLORS['bg_primary'])
    ajuda_window.resizable(True, True)

    # Frame principal com scrollbar
    main_frame = tk.Frame(ajuda_window, bg=COLORS['bg_primary'])
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # Área de texto com scrollbar
    text_frame = tk.Frame(main_frame, bg=COLORS['bg_primary'])
    text_frame.pack(fill=tk.BOTH, expand=True)

    text_widget = tk.Text(text_frame,
                         bg=COLORS['bg_secondary'],
                         fg=COLORS['text_primary'],
                         font=('Consolas', 10),
                         wrap=tk.WORD,
                         insertbackground=COLORS['accent_cyan'],
                         selectbackground=COLORS['accent_cyan'],
                         selectforeground=COLORS['bg_primary'])
    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_widget.config(yscrollcommand=scrollbar.set)

    # Insere o texto de ajuda
    text_widget.insert(tk.END, ajuda_texto)
    text_widget.config(state=tk.DISABLED)  # Torna somente leitura

    # Botão de fechar
    btn_fechar = ttk.Button(main_frame,
                           text="Fechar",
                           command=ajuda_window.destroy)
    btn_fechar.pack(pady=(10, 0))

    # Mantém a janela na frente e dá foco
    ajuda_window.transient()  # Corrected from transpose()
    ajuda_window.focus_set()
    ajuda_window.grab_set()  # Torna modal

def atualizar_status_tempo_real(status_label, last_update_label):
    """Atualiza o status em tempo real"""
    def atualizar():
        while True:
            try:
                current_time = datetime.now().strftime("%H:%M:%S")
                last_update_label.config(text=f"Última atualização: {current_time}")
                time.sleep(1)
            except:
                break

    thread = threading.Thread(target=atualizar, daemon=True)
    thread.start()

def atualizar_saldo_usdt(usdt_label):
    """Atualiza o saldo USDT lendo do arquivo de log"""
    def atualizar():
        while True:
            try:
                # Tenta ler o saldo do arquivo de log
                saldo_usdt = "0,00"
                try:
                    with open('erros_sistema.txt', 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # Procura pela última linha que contém "Saldo inicial USDT:" ou similar
                        for line in reversed(lines):
                            if "Saldo inicial USDT:" in line or "Saldo USDT disponível:" in line:
                                # Extrai o valor numérico
                                import re
                                match = re.search(r'[\d,]+\.\d+', line)
                                if match:
                                    saldo_str = match.group()
                                    # Converte para formato brasileiro (vírgula como separador decimal)
                                    saldo_float = float(saldo_str)
                                    saldo_usdt = f"{saldo_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                                    break
                except FileNotFoundError:
                    pass  # Arquivo de log ainda não existe
                except Exception:
                    pass  # Erro na leitura, mantém o valor anterior

                # Atualiza o label na thread principal (usa after para thread safety)
                def update_label():
                    usdt_label.config(text=f"$ {saldo_usdt}")

                # Agenda a atualização na thread principal da GUI
                # Isso é seguro porque usamos o método after do tkinter
                if 'usdt_label' in locals() and usdt_label.winfo_exists():
                    usdt_label.after(0, update_label)

                time.sleep(5)  # Atualiza a cada 5 segundos
            except:
                break

    thread = threading.Thread(target=atualizar, daemon=True)
    thread.start()

def criar_interface_moderna():
    """Cria a interface gráfica moderna e futurista"""
    # Configuração da Janela Principal
    root = tk.Tk()
    root.title("⚡ MERCADOIA PRO - Trading System v2.1")
    root.geometry("900x600")
    root.minsize(800, 500)
    root.configure(bg=COLORS['bg_primary'])

    # Tentar definir ícone (se disponível)
    try:
        root.iconbitmap(default='icon.ico')  # Opcional: colocar um ícone
    except:
        pass  # Ignorar se não houver ícone

    # Aplicar tema futurista
    aplicar_tema_futurista(root)

    # Frame principal com padding
    main_frame = tk.Frame(root, bg=COLORS['bg_primary'])
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # Cabeçalho com título e status
    header_frame = tk.Frame(main_frame, bg=COLORS['bg_primary'])
    header_frame.pack(fill=tk.X, pady=(0, 20))

    # Título principal
    title_label = tk.Label(header_frame,
                          text="⚡ MERCADOIA PRO",
                          font=('Segoe UI', 24, 'bold'),
                          fg=COLORS['accent_cyan'],
                          bg=COLORS['bg_primary'])
    title_label.pack(side=tk.LEFT)

    # Subtítulo
    subtitle_label = tk.Label(header_frame,
                             text="Sistema Automatizado de Trading",
                             font=('Segoe UI', 10),
                             fg=COLORS['text_secondary'],
                             bg=COLORS['bg_primary'])
    subtitle_label.pack(side=tk.LEFT, padx=(10, 0), pady=(10, 0))

    # Indicador de status do sistema (lado direito)
    status_frame = tk.Frame(header_frame, bg=COLORS['bg_primary'])
    status_frame.pack(side=tk.RIGHT)

    # Status do robô
    status_label = tk.Label(status_frame,
                           text="🔴 SISTEMA OFFLINE",
                           font=('Segoe UI', 10, 'bold'),
                           fg=COLORS['accent_red'],
                           bg=COLORS['bg_primary'])
    status_label.pack(anchor=tk.E)

    # Última atualização
    last_update_label = tk.Label(status_frame,
                                text="Aguardando inicialização...",
                                font=('Segoe UI', 8),
                                fg=COLORS['text_muted'],
                                bg=COLORS['bg_primary'])
    last_update_label.pack(anchor=tk.E)

    # Iniciar atualização de tempo real
    atualizar_status_tempo_real(status_label, last_update_label)

    # Notebook (abas) com estilo moderno
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

    # Aba de Controle Principal
    tab_controle = ttk.Frame(notebook)
    notebook.add(tab_controle, text="  📊 CONTROLE PRINCIPAL  ")

    # Aba de Logs
    tab_logs = ttk.Frame(notebook)
    notebook.add(tab_logs, text="  📋 LOGS DO SISTEMA  ")

    # Aba de Relatórios
    tab_relatorios = ttk.Frame(notebook)
    notebook.add(tab_relatorios, text="  📈 RELATÓRIOS  ")

    # Aba de Configurações
    tab_config = ttk.Frame(notebook)
    notebook.add(tab_config, text="  ⚙️ CONFIGURAÇÕES  ")

    # ===== ABA DE CONTROLE PRINCIPAL =====
    controle_frame = tk.Frame(tab_controle, bg=COLORS['bg_primary'])
    controle_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # Seção de Controle do Sistema
    controle_sistema_frame = tk.LabelFrame(controle_frame,
                                          text="⚙️ CONTROLE DO SISTEMA",
                                          bg=COLORS['bg_primary'],
                                          fg=COLORS['text_primary'])
    controle_sistema_frame.pack(fill=tk.X, pady=(0, 20))

    # Botões de controle do robô
    botoes_frame = tk.Frame(controle_sistema_frame, bg=COLORS['bg_primary'])
    botoes_frame.pack(fill=tk.X, padx=15, pady=15)

    btn_iniciar = ttk.Button(botoes_frame,
                            text="▶️ INICIAR ROBÔ",
                            style='Success.TButton',
                            command=lambda: iniciar_robo(status_label, btn_iniciar, btn_parar))
    btn_iniciar.pack(side=tk.LEFT, padx=(0, 10))

    btn_parar = ttk.Button(botoes_frame,
                          text="⏸️ PARAR ROBÔ",
                          style='Danger.TButton',
                          command=lambda: parar_robo(status_label, btn_iniciar, btn_parar),
                          state='disabled')
    btn_parar.pack(side=tk.LEFT, padx=(0, 10))

    # Botões de comandos de emergência
    cmd_frame = tk.Frame(controle_sistema_frame, bg=COLORS['bg_primary'])
    cmd_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

    ttk.Button(cmd_frame,
              text="🛑 EMERGÊNCIA: VENDER TUDO",
              style='Danger.TButton',
              command=lambda: enviar_comando("VENDA_TOTAL")).pack(side=tk.LEFT, padx=(0, 10))

    ttk.Button(cmd_frame,
              text="⏸️ PAUSAR",
              command=lambda: enviar_comando("PAUSAR")).pack(side=tk.LEFT, padx=(0, 10))

    ttk.Button(cmd_frame,
              text="▶️ RETOMAR",
              command=lambda: enviar_comando("RESUMIR")).pack(side=tk.LEFT)

    # Seção de Informações do Sistema
    info_frame = tk.LabelFrame(controle_frame,
                              text="📊 INFORMAÇÕES DO SISTEMA",
                              bg=COLORS['bg_primary'],
                              fg=COLORS['text_primary'])
    info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

    # Grid para informações
    info_grid = tk.Frame(info_frame, bg=COLORS['bg_primary'])
    info_grid.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

    # Labels para informações (serão atualizados dinamicamente)
    info_labels = {}

    info_items = [
        ("Status da Conexão:", "conexao_status", "Desconectado"),
        ("Último Sinal:", "ultimo_sinal", "Aguardando..."),
        ("Posições Abertas:", "posicoes_abertas", "0"),
        ("Saldo USDT:", "usdt_balance", "$ 0,00"),
        ("Taxa de Acerto:", "taxa_acerto", "0%"),
        ("Volatilidade do Mercado:", "volatilidade", "Baixa")
    ]

    for i, (label_text, key, default_value) in enumerate(info_items):
        row = i // 2
        col = (i % 2) * 2

        label = tk.Label(info_grid,
                        text=label_text,
                        font=('Segoe UI', 9),
                        fg=COLORS['text_secondary'],
                        bg=COLORS['bg_primary'])
        label.grid(row=row, column=col, sticky='w', padx=(0, 5), pady=2)

        value_label = tk.Label(info_grid,
                              text=default_value,
                              font=('Segoe UI', 9, 'bold'),
                              fg=COLORS['text_primary'],
                              bg=COLORS['bg_primary'])
        value_label.grid(row=row, column=col+1, sticky='w', padx=(0, 20), pady=2)

        info_labels[key] = value_label

    # Iniciar atualização do saldo USDT em tempo real
    atualizar_saldo_usdt(info_labels['usdt_balance'])

    # Seção de Ferramentas Rápidas
    ferramentas_frame = tk.LabelFrame(controle_frame,
                                     text="🔧 FERRAMENTAS RÁPIDAS",
                                     bg=COLORS['bg_primary'],
                                     fg=COLORS['text_primary'])
    ferramentas_frame.pack(fill=tk.X)

    ferramentas_buttons = tk.Frame(ferramentas_frame, bg=COLORS['bg_primary'])
    ferramentas_buttons.pack(fill=tk.X, padx=15, pady=15)

    ttk.Button(ferramentas_buttons,
              text="📋 VER LOGS DETALHADOS",
              command=lambda: abrir_script("monitors_log.py")).pack(side=tk.LEFT, padx=(0, 10))

    ttk.Button(ferramentas_buttons,
              text="❓ AJUDA",
              command=lambda: mostrar_ajuda()).pack(side=tk.LEFT, padx=(0, 10))

    ttk.Button(ferramentas_buttons,
              text="📈 GERAR RELATÓRIO",
              command=lambda: abrir_script("view_report.py")).pack(side=tk.LEFT, padx=(0, 10))

    ttk.Button(ferramentas_buttons,
              text="💾 EXPORTAR DADOS",
              command=lambda: print("Funcionalidade em desenvolvimento")).pack(side=tk.LEFT)

    # SEÇÃO DE LINHA DE COMANDO
    comando_frame = tk.LabelFrame(controle_frame,
                                 text="💻 LINHA DE COMANDO",
                                 bg=COLORS['bg_primary'],
                                 fg=COLORS['text_primary'])
    comando_frame.pack(fill=tk.X, pady=(10, 0))

    comando_input_frame = tk.Frame(comando_frame, bg=COLORS['bg_primary'])
    comando_input_frame.pack(fill=tk.X, padx=15, pady=10)

    tk.Label(comando_input_frame,
            text="$",
            font=('Consolas', 12, 'bold'),
            fg=COLORS['accent_cyan'],
            bg=COLORS['bg_primary']).pack(side=tk.LEFT, padx=(0, 10))

    comando_entry = tk.Entry(comando_input_frame,
                            font=('Consolas', 10),
                            width=40)
    comando_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    comando_entry.focus()

    def processar_comando(event=None):
        cmd = comando_entry.get().strip().lower()
        comando_entry.delete(0, tk.END)

        if not cmd:
            return "break"

        # Adiciona comando ao histórico de saída
        output_text.insert(tk.END, f"$ {cmd}\n")

        if cmd == "help":
            output_text.insert(tk.END, """COMANDOS DISPONÍVEIS:
help          - Mostra esta ajuda
status        - Mostra status atual do sistema
start         - Inicia o robô de trading
stop          - Para o robô de trading
pause         - Pausa novas operações
resume        - Retoma operações pausadas
sellall       - Vende imediatamente todas as posições
set symbol XXXUSDT  - Define par de trading (ex: set symbol SOLUSDT)
set risk X.X        - Define percentual de risco por trade (ex: set risk 2.5)
clear         - Limpa esta tela de comando
exit          - Fecha apenas esta janela de comando

EXEMPLOS:
$ start
$ set symbol ETHUSDT
$ set risk 3.0
$ status
""")
        elif cmd == "status":
            # Tenta ler o status dos logs
            try:
                with open('erros_sistema.txt', 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    status_line = "Status: Aguardando dados..."
                    for line in reversed(lines[-20:]):  # Últimas 20 linhas
                        if "Sistema inicializado" in line:
                            status_line = line.strip()
                            break
                        elif "Saldo inicial" in line:
                            status_line = line.strip()
                            break
                    output_text.insert(tk.END, f"{status_line}\n\n")
            except FileNotFoundError:
                output_text.insert(tk.END, "Status: Arquivo de log não encontrado ainda.\n\n")
            except Exception as e:
                output_text.insert(tk.END, f"Erro ao ler status: {str(e)}\n\n")
        elif cmd == "start":
            output_text.insert(tk.END, "Iniciando robô de trading...\n\n")
            iniciar_robo(status_label, btn_iniciar, btn_parar)
        elif cmd == "stop":
            output_text.insert(tk.END, "Parando robô de trading...\n\n")
            parar_robo(status_label, btn_iniciar, btn_parar)
        elif cmd == "pause":
            output_text.insert(tk.END, "Pausando operações...\n\n")
            enviar_comando("PAUSAR")
        elif cmd == "resume":
            output_text.insert(tk.END, "Retomando operações...\n\n")
            enviar_comando("RESUMIR")
        elif cmd == "sellall":
            output_text.insert(tk.END, "Executando venda total de todas as posições...\n\n")
            enviar_comando("VENDA_TOTAL")
        elif cmd.startswith("set symbol "):
            symbol = cmd[11:].strip().upper()
            if symbol.endswith('USDT') and len(symbol) >= 5:
                output_text.insert(tk.END, f"Símbolo de trading definido para: {symbol}\n")
                output_text.insert(tk.END, "NOTA: Esta alteração terá efeito na próxima inicialização do robô.\n\n")
                # Armazena para usar na próxima inicialização
                global symbol_override_temp
                symbol_override_temp = symbol
            else:
                output_text.insert(tk.END, "Erro: Formato de símbolo inválido. Use XXXUSDT (ex: SOLUSDT)\n\n")
        elif cmd.startswith("set risk "):
            try:
                risk_val = float(cmd[9:].strip())
                if 0.1 <= risk_val <= 20.0:
                    output_text.insert(tk.END, f"Percentual de risco definido para: {risk_val}%\n")
                    output_text.insert(tk.END, "NOTA: Esta alteração terá efeito na próxima inicialização do robô.\n\n")
                    # Armazena para usar na próxima inicialização
                    global risk_override_temp
                    risk_override_temp = risk_val
                else:
                    output_text.insert(tk.END, "Erro: O risco deve estar entre 0.1% e 20.0%\n\n")
            except ValueError:
                output_text.insert(tk.END, "Erro: Valor de risco inválido. Use um número (ex: 2.5)\n\n")
        elif cmd == "clear":
            output_text.delete(1.0, tk.END)
        elif cmd == "exit":
            # Fecha apenas esta janela de comando (não implementado como janela separada)
            output_text.insert(tk.END, "Prompt de comando encerrado. Use novamente quando necessário.\n\n")
        else:
            output_text.insert(tk.END, f"Comando não reconhecido: '{cmd}'. Digite 'help' para ver os comandos disponíveis.\n\n")

        output_text.see(tk.END)
        return "break"

    comando_entry.bind("<Return>", processar_comando)

    btn_executar = ttk.Button(comando_input_frame,
                             text="Executar",
                             command=processar_comando)
    btn_executar.pack(side=tk.LEFT, padx=(5, 0))

    # Área de saída de comandos
    output_frame = tk.Frame(comando_frame, bg=COLORS['bg_primary'])
    output_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

    output_text = tk.Text(output_frame,
                         bg=COLORS['bg_secondary'],
                         fg=COLORS['text_primary'],
                         font=('Consolas', 9),
                         wrap=tk.WORD,
                         height=8)
    output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    output_scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=output_text.yview)
    output_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    output_text.config(yscrollcommand=output_scrollbar.set)

    # Mensagem inicial
    output_text.insert(tk.END, "MERCADOIA PRO - LINHA DE COMANDO\n")
    output_text.insert(tk.END, "Digite 'help' para ver os comandos disponíveis\n\n")
    output_text.config(state=tk.NORMAL)

    # ===== ABA DE LOGS =====
    logs_frame = tk.Frame(tab_logs, bg=COLORS['bg_primary'])
    logs_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    logs_label = tk.Label(logs_frame,
                         text="📋 MONITOR DE LOGS EM TEMPO REAL",
                         font=('Segoe UI', 14, 'bold'),
                         fg=COLORS['accent_cyan'],
                         bg=COLORS['bg_primary'])
    logs_label.pack(pady=(0, 15))

    # Área de texto para logs com scrollbar
    logs_text_frame = tk.Frame(logs_frame, bg=COLORS['bg_primary'])
    logs_text_frame.pack(fill=tk.BOTH, expand=True)

    logs_text = tk.Text(logs_text_frame,
                       bg=COLORS['bg_secondary'],
                       fg=COLORS['text_primary'],
                       font=('Consolas', 9),
                       wrap=tk.WORD,
                       insertbackground=COLORS['accent_cyan'],
                       selectbackground=COLORS['accent_cyan'],
                       selectforeground=COLORS['bg_primary'])
    logs_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    logs_scrollbar = ttk.Scrollbar(logs_text_frame, orient=tk.VERTICAL, command=logs_text.yview)
    logs_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    logs_text.config(yscrollcommand=logs_scrollbar.set)

    # Botões de controle dos logs
    logs_ctrl_frame = tk.Frame(logs_frame, bg=COLORS['bg_primary'])
    logs_ctrl_frame.pack(fill=tk.X, pady=(10, 0))

    ttk.Button(logs_ctrl_frame,
              text="🗑️ LIMPAR LOGS",
              command=lambda: logs_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=(0, 10))

    ttk.Button(logs_ctrl_frame,
              text="💾 SALVAR LOGS",
              command=lambda: print("Salvando logs...")).pack(side=tk.LEFT)

    # Adicionar texto inicial aos logs
    logs_text.insert(tk.END, "[SISTEMA] MercadoIA Pro v2.1 inicializado\n")
    logs_text.insert(tk.END, "[SISTEMA] Aguardando conexão com o módulo de trading...\n")
    logs_text.insert(tk.END, "[SISTEMA] Interface gráfica carregada com tema futurista\n")
    logs_text.see(tk.END)

    # ===== ABA DE RELATÓRIOS =====
    relatorios_frame = tk.Frame(tab_relatorios, bg=COLORS['bg_primary'])
    relatorios_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    relatorio_title = tk.Label(relatorios_frame,
                              text="📈 CENTRO DE RELATÓRIOS",
                              font=('Segoe UI', 16, 'bold'),
                              fg=COLORS['accent_cyan'],
                              bg=COLORS['bg_primary'])
    relatorio_title.pack(pady=(0, 20))

    # Grid de botões de relatório
    relatorio_grid = tk.Frame(relatorios_frame, bg=COLORS['bg_primary'])
    relatorio_grid.pack(fill=tk.X, pady=10)

    relatorio_buttons = [
        ("📊 Relatório Diário", "Gerar relatório de desempenho do dia"),
        ("📉 Gráfico de Performance", "Visualizar evolução do patrimônio"),
        ("🎯 Análise de Trades", "Detalhar entradas e saídas"),
        ("⚠️ Relatório de Riscos", "Análise de exposição e drawdown"),
        ("📋 Histórico Completo", "Exportar todo o histórico de operações"),
        ("🔮 Projeções Futuras", "Simular cenários de mercado")
    ]

    for i, (texto, descricao) in enumerate(relatorio_buttons):
        row = i // 2
        col = i % 2

        btn_frame = tk.Frame(relatorio_grid, bg=COLORS['bg_tertiary'], relief=tk.RAISED, bd=1)
        btn_frame.grid(row=row, column=col, padx=5, pady=5, sticky="ew")

        btn = tk.Button(btn_frame,
                       text=texto,
                       font=('Segoe UI', 9, 'bold'),
                       bg=COLORS['bg_tertiary'],
                       fg=COLORS['text_primary'],
                       activebackground=COLORS['accent_cyan'],
                       activeforeground=COLORS['bg_primary'],
                       relief=tk.FLAT,
                       padx=10,
                       pady=8,
                       cursor="hand2")
        btn.pack(fill=tk.X)

        # Tooltip simples (mostrar descrição ao passar o mouse)
        def create_tooltip(widget, text):
            def enter(event):
                widget.config(bg=COLORS['bg_tertiary'])
            def leave(event):
                widget.config(bg=COLORS['bg_tertiary'])
            widget.bind("<Enter>", enter)
            widget.bind("<Leave>", leave)

        create_tooltip(btn, descricao)

    # Configurar expansão das colunas
    relatorio_grid.columnconfigure(0, weight=1)
    relatorio_grid.columnconfigure(1, weight=1)

    # ===== ABA DE CONFIGURAÇÕES =====
    config_frame = tk.Frame(tab_config, bg=COLORS['bg_primary'])
    config_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    config_title = tk.Label(config_frame,
                           text="⚙️ CENTRO DE CONFIGURAÇÕES",
                           font=('Segoe UI', 16, 'bold'),
                           fg=COLORS['accent_cyan'],
                           bg=COLORS['bg_primary'])
    config_title.pack(pady=(0, 20))

    # Notebook interno para configurações
    config_notebook = ttk.Notebook(config_frame)
    config_notebook.pack(fill=tk.BOTH, expand=True)

    # Aba de Parâmetros de Trading
    tab_trading = ttk.Frame(config_notebook)
    config_notebook.add(tab_trading, text="  📈 TRADING  ")

    # Aba de Gestão de Risco
    tab_risco = ttk.Frame(config_notebook)
    config_notebook.add(tab_risco, text="  ⚠️ RISCO  ")

    # Aba de Conexão
    tab_conexao = ttk.Frame(config_notebook)
    config_notebook.add(tab_conexao, text="  🔗 CONEXÃO  ")

    # Preencher abas de configuração com placeholders
    for tab_name, tab_frame in [("Parâmetros de Trading", tab_trading),
                               ("Gestão de Risco", tab_risco),
                               ("Conexão", tab_conexao)]:
        label = tk.Label(tab_frame,
                        text=f"Configurações de {tab_name}\n\n(Em desenvolvimento - versão futura)",
                        font=('Segoe UI', 11),
                        fg=COLORS['text_secondary'],
                        bg=COLORS['bg_primary'])
        label.pack(expand=True)

    # Rodapé informativo
    footer_frame = tk.Frame(main_frame, bg=COLORS['bg_primary'])
    footer_frame.pack(fill=tk.X, pady=(10, 0))

    footer_label = tk.Label(footer_frame,
                           text="© 2026 MercadoIA Pro • Desenvolvido para trading profissional • Versão 2.1.0",
                           font=('Segoe UI', 8),
                           fg=COLORS['text_muted'],
                           bg=COLORS['bg_primary'])
    footer_label.pack()

    # Iniciar a aplicação
    root.mainloop()

if __name__ == "__main__":
    criar_interface_moderna()