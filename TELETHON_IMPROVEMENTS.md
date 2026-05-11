# Melhorias de Telethon - Solução de Expiração de Sessão

## 🎯 O Problema Original

A sessão Telethon expirava porque:
- Sem monitoramento de conexão
- Sem reconexão automática
- Sem refresh periódico da sessão
- Sem tratamento de erros de desconexão

## ✅ Soluções Implementadas

### 1. **SessionManager** (novo arquivo)
Um gerenciador de sessão com:
- ✅ **Reconexão automática** com backoff exponencial (até 10 tentativas)
- ✅ **Monitoramento contínuo** a cada 30 segundos
- ✅ **Refresh automático** da sessão a cada 1 hora
- ✅ **Validação de autorização** após reconectar
- ✅ **Tratamento inteligente de erros**

### 2. **Telethon com Auto-Reconexão**
Configuração otimizada:
```python
client = TelegramClient(
    session,
    api_id=API_ID,
    api_hash=API_HASH,
    auto_reconnect=True,      # Reconexão automática nativa
    connection_retries=5,      # 5 tentativas de conexão
    retry_delay=3,             # Delay de 3 segundos entre tentativas
)
```

### 3. **Persistência de Sessão**
- Sessão salva no MongoDB após cada conexão bem-sucedida
- Timestamp de atualização para rastreamento
- Recuperação automática na inicialização

### 4. **Shutdown Graciosa**
- Salva sessão antes de desconectar
- Manipula sinais SIGINT e SIGTERM
- Encerramento ordenado

---

## 📊 Fluxo de Funcionamento

```
┌─────────────────────────────────────────┐
│  main.py inicia                         │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  SessionManager.connect()               │
│  - Recupera sessão do MongoDB           │
│  - Conecta ao Telegram                  │
│  - Valida autorização                   │
│  - Salva sessão atualizada              │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Registra handlers e inicia bot         │
└────────────┬────────────────────────────┘
             │
             ▼
  ┌─ Paralelamente ─┐
  │                 │
  ▼                 ▼
client.run_     maintain_connection()
until_          - A cada 30s: verifica status
disconnected()  - Se desconectado: reconecta
                - A cada 1h: refresh de sessão
```

---

## 🚀 Como Usar

### Execução Normal

```bash
python main.py
```

**O bot agora:**
- Reconecta automaticamente se perder conexão
- Atualiza a sessão periodicamente
- Monitora continuamente a conexão
- Encerra graciosamente com `Ctrl+C`

### O que Esperar nos Logs

#### Inicialização Bem-sucedida:
```
2026-05-11 14:30:00 [INFO] __main__: ============================================================
2026-05-11 14:30:00 [INFO] __main__: 🤖 Telegram Keyword Monitor Bot - Versão com Auto-Reconexão
2026-05-11 14:30:00 [INFO] __main__: ============================================================
2026-05-11 14:30:00 [INFO] session_manager: Iniciando gerenciador de sessão...
2026-05-11 14:30:01 [INFO] session_manager: ✅ Autenticado como: João Silva (id=123456)
2026-05-11 14:30:01 [INFO] __main__: ✅ Bot ativo. Monitorando palavras-chave...
```

#### Reconexão Automática (se desconectar):
```
2026-05-11 14:35:30 [WARNING] session_manager: ⚠️  Conexão perdida! Tentando reconectar...
2026-05-11 14:35:35 [INFO] session_manager: 🔄 Tentativa de reconexão 1/10 em 5 segundos...
2026-05-11 14:35:40 [INFO] session_manager: ✅ Reconectado com sucesso!
```

#### Atualização Automática de Sessão (a cada 1 hora):
```
2026-05-11 15:30:01 [DEBUG] session_manager: ✓ Sessão salva no MongoDB
```

---

## ⚙️ Configurações Personalizáveis

Em `session_manager.py`, você pode ajustar:

```python
MAX_RECONNECT_ATTEMPTS = 10      # Máximo de tentativas de reconexão
RECONNECT_DELAY = 5              # Delay inicial em segundos (dobra a cada tentativa)
SESSION_REFRESH_INTERVAL = 3600  # Refresh de sessão a cada 1 hora (3600s)
```

---

## 🔍 Monitoramento da Sessão

### Ver quando a sessão foi atualizada:

```bash
mongosh "mongodb+srv://user:pass@cluster.mongodb.net"
# No MongoDB:
db.telegram_keyword_bot.session.findOne()
```

Você verá algo como:
```json
{
  "_id": "session",
  "value": "1a2b3c4d...",
  "updated_at": ISODate("2026-05-11T14:30:01.000Z"),
  "expires_at": null
}
```

---

## 🐛 Troubleshooting

### "Sessão expirada"
- A sessão pode ter expirado se o bot ficou offline por muito tempo
- Execute `python setup_session.py` novamente

### "Conexão perdida repetidamente"
- Verifique sua internet
- Pode ser um problema com Telegram em sua região
- Tente aumentar `RECONNECT_DELAY`

### "Bot não reconecta"
- Verifique se o token de 2FA ainda é válido
- Verifique os logs para mensagens de erro

---

## 📈 Benefícios desta Solução

✅ **Sem expiração forçada** — Sessão é mantida viva automaticamente  
✅ **Resiliente** — Se perder internet, reconecta sozinho  
✅ **Confiável** — Monitoramento contínuo  
✅ **Simples** — Sem código extra no projeto principal  
✅ **Escalável** — Funciona para múltiplos bots  

---

## 🔗 Referências

- [Telethon Documentation](https://docs.telethon.dev/)
- [StringSession](https://docs.telethon.dev/en/latest/basic/sessions.html#string-session)
- [Auto-Reconnect](https://docs.telethon.dev/en/latest/basic/errors.html)
