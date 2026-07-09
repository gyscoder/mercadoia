# MercadoIA Trading Bot

Sistema de trading automatizado para Binance com interface gráfica moderna, capaz de operar com trading real em USDT e modulação de risco profissional.

## ✨ Funcionalidades

- 💹 **Trading Real em USDT**: Operação com dinheiro real na Binance (USDT pairs)
- 🛡️ **Gestão de Risco Profissional**: 
  - 2% de risco por trade
  - 5% de limite de perda diária
  - Position sizing dinâmico baseado no saldo
- 🖥️ **Interface Gráfica Moderna**: 
  - Tema futurista profissional com cores cyan/roxo
  - Abas organizadas: Controle Principal, Logs, Relatórios, Configurações
  - Linha de comando interativa com prompt "$" para controle avançado
  - Atualização em tempo real de saldo, status e métricas
- 📊 **Sistema de Relatórios Completo**:
  - Relatórios diários de performance
  - Histórico de trades com análise detalhada
  - Gráficos de evolução patrimônio e análise de riscos
  - Exportação de dados para análise externa
- ⚙️ **Configuração Flexível**:
  - Abas de configuração para parâmetros de trading, gestão de risco e conexão
  - Suporte a múltiplos símbolos via watchlist configurável
  - Modo testnet/live toggleável para testes seguros
- 🔐 **Segurança de nível empresarial**:
  - Autenticação segura via HMAC-SHA256 com API Keys
  - Credenciais protegidas em .env (nunca versionadas)
  - Logging criptografado e auditoria completa
  - Comandos de emergência (VENDER TUDO, PAUSAR, etc.)

## 📁 Estrutura do Projeto

```
mercadoia/
├── gui.py                    # Interface gráfica principal (Tkinter)
├── main_real.py              # Sistema de trading real (USDT-based)
├── exchange_api.py           # Cliente seguro para Binance API
├── data_engine.py            # Gerenciamento de banco de dados e estado
├── strategy.py               # Lógica de decisão de trading
├── detect_patterns_with_alerts.py # Detecção de padrões técnicos
├── view_report.py            # Gerador de relatórios de performance
├── monitors_log.py           # Monitor de logs em tempo real
├── config.py                 # Configurações constantes (WATCHLIST, parâmetros)
├── memoria_mvp.md            # Documentação detalhada da implementação
├── memoria.md                # Documentação original do projeto
├── market_data.db            # Banco de dados SQLite (local, não versionado)
├── .env                      # Variáveis de ambiente (API Keys - NÃO versionado)
└── README.md                 # Este arquivo
```

## 🚀 Como Começar

### Pré-requisitos
- Python 3.8+
- Conta na Binance com API Key e Secret ativadas para trading
- Conta no Windows 10/11 (otimizado para ambiente Windows)

### Instalação
1. Clone o repositório:
   ```bash
   git clone https://github.com/gyscoder/mercadoia.git
   cd mercadoia
   ```

2. Instale as dependências:
   ```bash
   pip install pandas python-dotenv
   ```

3. Configure suas credenciais:
   - Copie `.env.example` para `.env` (ou crie um novo arquivo `.env`)
   - Adicione suas chaves da Binance:
     ```
     BINANCE_API_KEY=sua_chave_aqui
     BINANCE_API_SECRET=seu_secret_aqui
     ```
   - **IMPORTANTE**: Nunca compartilhe ou versionar o arquivo `.env`

4. Inicialize o banco de dados (primeira execução):
   ```bash
   python resetdb.py
   ```

### Modo de Uso
#### Interface Gráfica (Recomendado)
```bash
python gui.py
```
- Use a aba "Controle Principal" para iniciar/parar o robô
- A linha de comando "$" permite controle avançado (digite `help` para ver comandos)
- Monitore o saldo USDT em tempo real na aba de informações
- Gere relatórios na aba "Relatórios"

#### Linha de Comando Direta
```bash
# Trading com símbolos padrão da watchlist
python main_real.py

# Especificar símbolo individual
python main_real.py --symbol SOLUSDT

# Modo testnet para testes seguros (altere em main_real.py)
# Defina testnet = True na linha de inicialização da BinanceAPI
```

### Comandos da Linha de Comando (na GUI)
Digite na prompt "$" da interface:
- `help` - Mostra todos os comandos disponíveis
- `status` - Mostra status atual do sistema
- `start` - Inicia o robô de trading
- `stop` - Para o robô de trading
- `pause` - Pausa novas operações
- `resume` - Retoma operações pausadas
- `sellall` - Vende imediatamente todas as posições (emergência)
- `set symbol XXXUSDT` - Define par de trading (ex: `set symbol BTCUSDT`)
- `set risk X.X` - Define percentual de risco por trade (ex: `set risk 2.5`)
- `clear` - Limpa a tela de comando
- `exit` - Fecha o prompt de comando

## ⚙️ Configuração

### Parâmetros de Trading (em `config.py`)
- `WATCHLIST`: Lista de símbolos para monitoramento (padrão: ['BTCUSDT', 'ETHUSDT'])
- `TAKE_PROFIT_PCT`: Percentual de take profit (padrão: 1.5%)
- `STOP_LOSS_PCT`: Percentual de stop loss (padrão: 1.0%)
- `INTERVALO_MONITORAMENTO`: Intervalo em segundos entre verificações (padrão: 10)

### Gestão de Risco (em `main_real.py`)
- `MAX_RISK_PER_TRADE`: 0.02 (2% do saldo USDT por trade)
- `MAX_DAILY_LOSS`: 0.05 (5% de perda diária máxima)
- Ajuste esses valores conforme seu perfil de risco

### Segurança
- O sistema opera com **dinheiro real** - comece com valores baixos para teste
- Todas as chaves de API são carregadas de forma segura via variáveis de ambiente
- Nenhum dado sensível é armazenado em logs ou banco de dados
- Use o modo testnet inicialmente para validar estratégias sem risco

## 📈 Performance e Relatórios

O sistema gera relatórios automáticos incluindo:
- **Relatório Diário**: Performance do dia com win/loss ratio
- **Histórico de Trades**: Detalhe de todas operações com timestamps
- **Análise de Riscos**: Drawdown, exposição por símbolo, taxa de acerto
- **Projeções Futuras**: Simulação baseado em desempenho histórico

Acesse relatórios via:
- Interface gráfica → Aba "Relatórios" → Botões específicos
- Linha de comando: `python view_report.py`

## 🛡️ Avisos de Segurança

⚠️ **IMPORTANTE: LEIA ANTES DE USAR**

1. **Este sistema opera com DINHEIRO REAL** - Use apenas capital que você pode perder
2. Sempre comece com valores mínimos para testar suas estratégias
3. Monitore continuamente os logs durante as operações
4. Nunca compartilhe seu arquivo `.env` ou expõe suas chaves de API
5. A Binance não é responsável por perdas decorrentes do uso de bots de terceiros
6. Consulte um profissional financeiro antes de operações de alto valor
7. Este é um software educacional - não constituye aconselhamento financeiro

## 🔧 Manutenção

- Atualize regularmente suas dependências: `pip install --upgrade -r requirements.txt`
- Verifique periodicamente por atualizações na API da Binance
- Faça backup do seu `market_data.db` semanalmente
- Revise suas estratégias a cada mês baseado nos relatórios de performance

## 👥 Contribuindo

Este projeto está atualmente em desenvolvimento privado para portfólio. 
Sinta-se à vontade para:
- Fazer fork do repositório
- Sugerir melhorias via issues
- Enviar pull requests com correções de bugs

## 📄 Licença

Este projeto é licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- Binance por fornecer uma API robusta e documentada
- Comunidade open-source por bibliotecas como pandas, python-dotenv
- Todos os traders que compartilharam conhecimento sobre gestão de risco

---

**MercadoIA Trading Bot v2.1**  
Desenvolvido para traders profissionais que valorizam tecnologia e segurança  
© 2026 gyscoder - Todos os direitos reservados