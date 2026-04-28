# Guia de Contribuição

Obrigado por considerar contribuir com este projeto! Este documento fornece diretrizes para manter o código limpo, organizado e fácil de manter.

---

## Código de Conduta

- Seja respeitoso com outros colaboradores
- Abra issues e PRs de boa fé
- Forneça contexto claro e detalhado
- Aceite críticas construtivas

---

## Como Contribuir

### Reportando Bugs

Encontrou um bug? Abra uma **Issue** no GitHub:

1. **Verifique** se o bug já não foi reportado
2. **Descreva o problema** de forma clara e concisa
3. **Passos para reproduzir:**
   ```
   1. Execute ...
   2. Observe que ...
   3. Esperado: ...
   ```
4. **Esperado vs. Observado:** Qual era o comportamento esperado?
5. **Ambiente:**
   ```
   - Python: 3.9
   - OS: Windows 10
   - Telethon: 1.34.0
   ```

**Exemplo de issue bem formatada:**

```markdown
**Título:** Bot não recebe mensagens de canais privados

**Descrição:**
O bot está configurado corretamente e conectado, mas não monitora 
mensagens de canais privados.

**Passos para reproduzir:**
1. Adicione um canal privado à lista de monitoramento
2. Envie uma mensagem para aquele canal
3. Nenhum alerta é recebido no grupo de controle

**Esperado:**
O bot deveria encaminhar a mensagem e enviar um alerta

**Observado:**
Nada acontece, sem erros nos logs

**Ambiente:**
- Python 3.10
- Ubuntu 22.04
- Telethon 1.34.0
```

### Sugerindo Features

Tem uma ideia para melhorar o bot?

1. **Abra uma Issue** com o label `enhancement`
2. **Descreva a feature:** O que ela faria? Por que seria útil?
3. **Exemplos de uso:** Como seria usada?
4. **Possíveis implementações:** Tem ideias de como implementar?

**Exemplo de feature request:**

```markdown
**Título:** Adicionar suporte a expressões regulares em keywords

**Descrição:**
Permitir usar regex nos padrões de keyword para mais flexibilidade
ao invés de apenas text matching literal.

**Exemplo de uso:**
```
/adicionar python(3\.[0-9]+)?
/adicionar (machine|deep).*learning
```

**Benefício:**
Detectar variações de termos com uma única keyword
```

---

## Desenvolvendo Localmente

### 1. Setup do Ambiente

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/telegram-keyword-monitor-bot.git
cd telegram-keyword-monitor-bot

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Configure o .env
cp .env.example .env
# Edite com seus valores
```

### 2. Autentique com Telegram

```bash
python setup_session.py
```

### 3. Teste suas mudanças

```bash
python main.py
# Monitore os logs
```

### 4. Commit e Push

```bash
git checkout -b feature/sua-feature
# Faça suas mudanças
git add .
git commit -m "feat: descrição da sua feature"
git push origin feature/sua-feature
```

---

## Padrão de Commits

Seguimos [Conventional Commits](https://www.conventionalcommits.org/pt-br/). Isso padroniza a história de commits e facilita gerar changelogs.

### Formato

```
<tipo>(<escopo>): <assunto>

<corpo>

<rodapé>
```

### Tipos

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| `feat` | Nova funcionalidade | `feat(commands): adiciona /listar com paginação` |
| `fix` | Correção de bug | `fix(mongodb): trata erro de timeout` |
| `docs` | Documentação | `docs(readme): atualiza instruções de instalação` |
| `refactor` | Refatoração de código | `refactor(handlers): simplifica lógica de matching` |
| `test` | Adição de testes | `test(message_handler): adiciona testes de matching` |
| `chore` | Build, deps, etc | `chore(deps): atualiza telethon para 1.35.0` |
| `style` | Formatação | `style: adiciona type hints em mongodb.py` |

### Escopo (opcional)

Indica qual parte do código foi afetada:

- `config`
- `database` / `mongodb`
- `handlers` / `commands` / `messages`
- `logging`
- `setup`
- `docs`

### Exemplos Bons

```bash
# Feature simples
git commit -m "feat: monitora palavras-chave em tempo real"

# Com escopo
git commit -m "feat(commands): adiciona /listar para ver todas as keywords"

# Bug fix
git commit -m "fix(mongodb): trata erro de conexão interrompida"

# Com corpo explicativo
git commit -m "refactor(handlers): simplifica detecção de keywords

Remove código duplicado no message handler.
Melhora performance em ~15% com pre-compile de regex patterns."
```

### Exemplos Ruins

```bash
git commit -m "updated stuff"
git commit -m "fix bug"
git commit -m "changes in handlers and config files"
```

---

## Pull Request

Quando seu código estiver pronto, abra um **Pull Request**:

### Antes de abrir

- [ ] Código segue o style do projeto
- [ ] Testou localmente e funcionou
- [ ] Commits seguem Conventional Commits
- [ ] Documentação foi atualizada (se necessário)
- [ ] Sem conflitos com `main`

### Abrindo a PR

```markdown
## Descrição

Quais mudanças essa PR introduz? Por que foram feitas?

## Tipo de mudança

- [ ] Bug fix
- [ ] Nova feature
- [ ] Breaking change
- [ ] Documentação

## Como testar

Passos para verificar que a mudança funciona:

1. Execute setup_session.py
2. Inicie o bot com `python main.py`
3. Teste o comando `/adicionar test-keyword`
4. Verifique que o alerta é recebido

## Checklist

- [ ] Código testado localmente
- [ ] Logs ausentes de erros
- [ ] Documentação atualizada
- [ ] Sem warnings/errors
```

### Depois de abrir

- Responda aos comentários de review
- Faça alterações conforme solicitado
- Force push quando atualizar (evita múltiplos commits para feedback)

```bash
# Faça alterações
git add .
git commit -m "refactor: endereça feedback do review"
git push -f origin feature/sua-feature
```

---

## Dúvidas Frequentes

**P: Por onde começo?**  
R: Procure por issues com label `good first issue` ou `help wanted`.

**P: Como faço para que meu PR seja mergeado mais rápido?**  
R: Siga as guidelines, teste bem, commits descritivos e bom contexto na PR.

**P: Posso trabalhar em features grandes?**  
R: Sim! Abra uma issue primeiro para discussão. Features grandes são melhores em PRs menores.

**P: Preciso fazer rebase?**  
R: Se houver conflitos com `main`, sim. Caso contrário, não é necessário.

---

## Configuração de Desenvolvimento (Opcional)

### Linting com Ruff

```bash
pip install ruff
ruff check .
```

### Formatação com Black

```bash
pip install black
black .
```

### Type checking com Mypy

```bash
pip install mypy
mypy .
```

---

## Precisa de Ajuda?

- Abra uma Issue com a tag `question`
- Deixe um comentário em uma Issue existente
- Consulte o README para troubleshooting

---

## Reconhecimento

Contribuições são muito apreciadas! Você será reconhecido na documentação do projeto.

---

<div align="center">

Obrigado por ajudar a melhorar este projeto! 🎉

</div>
