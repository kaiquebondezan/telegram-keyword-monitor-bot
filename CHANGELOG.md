# Changelog

Todas as mudanças notáveis neste projeto são documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [1.0.0] - 2026-04-27

### Added

- **Monitoramento em tempo real de palavras-chave** — O bot detecta automaticamente keywords em mensagens de múltiplos chats e canais
- **Sistema de alertas inteligente** — Alertas detalhados com contexto completo (chat, usuário, horário)
- **Gerenciamento de keywords via comandos** — Adicione, remova e liste palavras-chave sem reiniciar o bot
  - `/adicionar <palavra>` — Adiciona uma nova palavra-chave
  - `/remover <palavra>` — Remove uma palavra-chave
  - `/listar` — Lista todas as palavras-chave monitoradas
  - `/ajuda` — Mostra help com todos os comandos
- **Persistência em MongoDB Atlas** — Armazenamento robusto de keywords e sessão Telegram
- **Autenticação segura com Telethon** — Usa session strings para autenticação segura com a conta pessoal
- **Logging estruturado** — Sistema de logs detalhado para debugging e monitoramento
- **Setup assistido** — Script `setup_session.py` para autenticação interativa na primeira execução
- **Arquitetura assíncrona** — Construído 100% com async/await para máxima concorrência
- **Tratamento de erros robusto** — Recuperação elegante de falhas de conexão e timeouts
- **Timezone support** — Alertas em horário local (BRT) configurable

### Technical Details

- **Backend:** Python 3.9+
- **Telegram API:** Telethon 1.34.0
- **Banco de dados:** MongoDB Atlas com Motor (driver async)
- **Autenticação:** python-dotenv para gerenciamento de credenciais
- **Estrutura:** Modular com separação de concerns (handlers, database, config)

### Features Principais

✨ Detecção case-insensitive de palavras-chave  
✨ Suporte a múltiplos chats/canais simultaneously  
✨ Encaminhamento automático de mensagens originais  
✨ Informações detalhadas do remetente (nome, username)  
✨ Índice único no MongoDB para evitar duplicação  
✨ Ignora automaticamente o grupo de controle para evitar loops  

---

## Roadmap para versões futuras

### Planejado

- [ ] Paginação para `/listar` com muitas keywords
- [ ] Busca/filtragem de histórico de alertas
- [ ] Palavras-chave com expressões regulares
- [ ] Notificações em diferentes canais (e-mail, Webhook)
- [ ] Dashboard web para visualizar estatísticas
- [ ] Exportar logs de alertas em CSV/JSON
- [ ] Suporte a múltiplas contas simultâneas
- [ ] Integração com Sentry para error tracking

---

## Notas de Versão

### v1.0.0

Primeira release estável com todas as features essenciais funcionando corretamente em produção. O bot foi testado em múltiplos cenários e ambientes.

**Como instalar v1.0.0:**

```bash
git clone https://github.com/seu-usuario/telegram-keyword-monitor-bot.git
cd telegram-keyword-monitor-bot
pip install -r requirements.txt
python setup_session.py
python main.py
```

Consulte o [README.md](README.md) para instruções detalhadas.

---

## Convenção de Commits

Este projeto segue [Conventional Commits](https://www.conventionalcommits.org/pt-br/):

- `feat:` nova funcionalidade
- `fix:` correção de bug
- `docs:` mudanças na documentação
- `refactor:` refatoração de código (sem mudança de funcionalidade)
- `test:` adição ou modificação de testes
- `chore:` atualizações de build, dependências, etc.

---

**Última atualização:** 27 de Abril de 2026
