# telegram-keyword-monitor-bot

<div align="center">

![Python](https://img.shields.io/badge/python-3.9%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)

Um bot Telegram inteligente para monitorar palavras-chave em chats e canais, com alertas automáticos em tempo real.

[Sobre](#sobre) • [Features](#features) • [Instalação](#instalação) • [Uso](#uso) • [Estrutura](#estrutura) • [Contribuindo](#contribuindo) • [Licença](#licença)

</div>

---

## Sobre

**telegram-keyword-monitor-bot** é um bot automático que monitora mensagens em múltiplos chats e canais do Telegram. Sempre que uma palavra-chave configurada é detectada, o bot encaminha a mensagem original para um grupo de controle e envia um alerta detalhado com informações como:

- A palavra-chave encontrada
- O chat onde a mensagem foi enviada
- Quem enviou a mensagem (nome e username, se disponível)
- Data e hora da detecção (em BRT)

**Problema resolvido:** Permite que você acompanhe tópicos ou termos específicos de interesse em diversos chats simultaneamente, sem precisar permanecer conectado em todos eles.

---

## Features

✨ **Monitoramento em Tempo Real** — Detecta palavras-chave instantaneamente em mensagens recebidas

🔔 **Alertas Detalhados** — Inclui contexto completo (chat, usuário, horário, conteúdo original)

📝 **Gerenciamento Dinâmico** — Adicione e remova palavras-chave sem reiniciar o bot

💾 **Persistência em MongoDB** — Palavras-chave e sessão armazenadas em banco de dados

🔐 **Autenticação Segura** — Usa Telethon com session strings para conectar com sua conta Telegram

🚀 **Assíncrono** — Construído com async/await para máxima eficiência

---

## Pré-requisitos

- **Python 3.9 ou superior**
- **Conta Telegram** (sua conta pessoal será usada como bot)
- **Chave API Telegram** (API_ID e API_HASH) — Obtenha em [my.telegram.org](https://my.telegram.org)
- **MongoDB Atlas** — Conta gratuita em [mongodb.com/cloud/atlas](https://mongodb.com/cloud/atlas)

---

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/telegram-keyword-monitor-bot.git
cd telegram-keyword-monitor-bot
```

### 2. Crie um ambiente virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# API Telegram — Obtenha em https://my.telegram.org
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890

# MongoDB Atlas — String de conexão
# Formato: mongodb+srv://usuario:senha@cluster.mongodb.net/?retryWrites=true&w=majority
MONGO_URI=mongodb+srv://seu-usuario:sua-senha@seu-cluster.mongodb.net/?retryWrites=true&w=majority

# ID do grupo de controle (use um grupo privado pessoal)
# Obtenha o ID usando: /id (de um bot que responde comandos)
CONTROL_GROUP_ID=-1001234567890
```

**Guia de variáveis de ambiente:**

| Variável | Tipo | Descrição | Exemplo |
|----------|------|-----------|---------|
| `API_ID` | int | ID da sua aplicação Telegram | `12345678` |
| `API_HASH` | string | Hash da sua aplicação Telegram | `abcdef1234567890abcdef1234567890` |
| `MONGO_URI` | string | String de conexão MongoDB Atlas | `mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority` |
| `CONTROL_GROUP_ID` | int | ID do grupo de controle (negativo para grupos) | `-1001234567890` |

---

## Como Usar

### 1. Configure a sessão Telegram

Execute este script uma única vez para autenticar com sua conta Telegram:

```bash
python setup_session.py
```

Siga as instruções na tela para confirmar o login. A sessão será salva automaticamente no MongoDB.

### 2. Inicie o bot

```bash
python main.py
```

Você deve ver logs indicando que o bot está ativo e aguardando mensagens.

### 3. Use os comandos no grupo de controle

Acesse o grupo privado configurado em `CONTROL_GROUP_ID` e use os comandos:

| Comando | Descrição |
|---------|-----------|
| `/ajuda` | Mostra a lista de comandos disponíveis |
| `/listar` | Lista todas as palavras-chave monitoradas |
| `/adicionar <palavra>` | Adiciona uma nova palavra-chave |
| `/remover <palavra>` | Remove uma palavra-chave |

**Exemplos:**

```
/adicionar python
/adicionar "machine learning"
/remover python
/listar
```

---

## Estrutura do Projeto

```
telegram-keyword-monitor-bot/
│
├── main.py                    # Entry point do bot, inicializa e mantém conexão
│
├── config.py                  # Carrega variáveis de ambiente
│
├── setup_session.py           # Script para autenticar com Telegram (uso único)
├── generate_session.py        # Utilitário para gerar nova sessão se necessário
│
├── database/                  # Gerenciamento do banco de dados
│   ├── __init__.py
│   └── mongodb.py             # Funções para conectar, consultar e persistir dados
│
├── handlers/                  # Manipuladores de eventos Telegram
│   ├── __init__.py
│   ├── command_handler.py     # Processa comandos (/listar, /adicionar, etc)
│   └── message_handler.py     # Monitora mensagens e detecta keywords
│
├── requirements.txt           # Dependências do projeto
├── .env.example               # Modelo de variáveis de ambiente
├── .gitignore                 # Arquivos ignorados no Git
├── LICENSE                    # Licença MIT
└── README.md                  # Este arquivo
```

### Descrição dos arquivos principais

**main.py** — Inicializa o bot, conecta ao MongoDB, restaura a sessão Telegram e registra os handlers de eventos.

**config.py** — Centraliza todas as configurações lidas do arquivo `.env` para fácil acesso.

**setup_session.py** — Realiza autenticação interativa com Telegram. Deve ser executado uma vez para gerar e salvar a sessão.

**database/mongodb.py** — Fornece funções assíncronas para:
- Conectar ao MongoDB Atlas
- Recuperar, adicionar e remover palavras-chave
- Gerenciar a session string

**handlers/command_handler.py** — Registra listeners para comandos específicos no grupo de controle.

**handlers/message_handler.py** — Monitora todas as mensagens recebidas, detecta keywords e envia alertas.

---

## Desenvolvendo Localmente

### 1. Clone e configure

```bash
git clone https://github.com/seu-usuario/telegram-keyword-monitor-bot.git
cd telegram-keyword-monitor-bot
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install -r requirements.txt
```

### 2. Configure o `.env`

Copie `.env.example` para `.env` e preencha com seus valores:

```bash
cp .env.example .env
# Edite .env com seus dados
```

### 3. Autentique com Telegram

```bash
python setup_session.py
```

### 4. Inicie o bot

```bash
python main.py
```

### 5. Monitorar logs

O bot mostra logs em tempo real no console. Você pode configurar diferentes níveis de log editando `main.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG, INFO, WARNING, ERROR
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
```

---

## Troubleshooting

**"Nenhuma sessão encontrada no MongoDB"**
- Execute `python setup_session.py` novamente para autenticar.

**"Sessão expirada"**
- Sua sessão do Telegram expirou. Execute `python setup_session.py` novamente.

**"Conexão com MongoDB falhou"**
- Verifique se `MONGO_URI` está correto.
- Verifique se seu IP está adicionado na whitelist do MongoDB Atlas.

**"Bot não recebe mensagens"**
- Verifique se o bot está autorizado em `main.py` (linha `if not await client.is_user_authorized()`).
- Certifique-se de que está monitorando os chats corretos.

---

## Como Contribuir

Contribuições são bem-vindas! Mesmo sendo um projeto pessoal, documentamos o processo para mantê-lo organizado:

### 1. Abra uma Issue

Antes de começar, abra uma **Issue** descrevendo o problema ou a feature que deseja adicionar:

- Seja específico: qual é o problema? qual é a solução proposta?
- Verifique se já não existe uma issue similar aberta.

### 2. Fork e crie uma branch

```bash
git checkout -b feature/sua-feature
# ou
git checkout -b fix/seu-bugfix
```

### 3. Commits com padrão

Siga o padrão **Conventional Commits**:

```bash
git commit -m "feat: adiciona comando /listar com paginação"
git commit -m "fix: corrige erro de timeout em conexão MongoDB"
git commit -m "docs: atualiza README com exemplos"
git commit -m "refactor: simplifica lógica de detecção de keywords"
git commit -m "test: adiciona testes para message_handler"
```

**Tipos comuns:**
- `feat:` nova feature
- `fix:` correção de bug
- `docs:` documentação
- `refactor:` refatoração de código
- `test:` adição de testes
- `chore:` atualizações de dependências

### 4. Faça um Pull Request

Quando terminar, abra um **Pull Request** com:

- Título descritivo
- Descrição do que foi mudado e por quê
- Referência à issue: `Closes #123`

### 5. Code Review

Seu PR será revisado e pode receber sugestões de melhorias.

---

## Licença

Este projeto está licenciado sob a **MIT License**. Veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## Contato & Suporte

Encontrou um bug? Tem uma sugestão? Abra uma **Issue** no repositório!

**Autor:** [Seu Nome/Usuário]  
**Repositório:** [github.com/seu-usuario/telegram-keyword-monitor-bot](https://github.com/seu-usuario/telegram-keyword-monitor-bot)

---

<div align="center">

Made with ❤️ by [Seu Nome]

</div>
