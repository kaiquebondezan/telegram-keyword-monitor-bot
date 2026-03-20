import os
import json
import threading
import asyncio
import time
from flask import Flask, jsonify
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

# --- CORREÇÃO PARA O PYTHON NO RENDER ---
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from pyrogram import Client, filters
from pyrogram.errors import ConnectionError as PyrogramConnectionError

# --- CREDENCIAIS ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
MEU_APP_ID = int(os.environ.get("MEU_APP_ID", 0))
MONGO_URI = os.environ.get("MONGO_URI")

# --- VALIDAÇÃO DE CREDENCIAIS ---
print("[LOG] Validando credenciais...")
CREDENCIAIS_OK = True
if not API_ID or not API_HASH or not SESSION_STRING or not MEU_APP_ID:
    print("[❌ ERRO] Alguma credencial do Telegram está vazia!")
    print(f"  API_ID: {bool(API_ID)}")
    print(f"  API_HASH: {bool(API_HASH)}")
    print(f"  SESSION_STRING: {bool(SESSION_STRING)}")
    print(f"  MEU_APP_ID: {MEU_APP_ID}")
    CREDENCIAIS_OK = False

if not MONGO_URI:
    print("[❌ ERRO] MONGO_URI não configurada! Configure no Render.")
    CREDENCIAIS_OK = False

# --- CONFIGURAÇÃO MONGODB (Com Timeout e Validação) ---
mongo_client = None
BANCO_DISPONIVEL = False

if MONGO_URI:
    try:
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
        # Testa a conexão
        mongo_client.admin.command('ping')
        db = mongo_client['monitor_bot_db']
        colecao = db['palavras_chave']
        BANCO_DISPONIVEL = True
        print("[✅] MongoDB conectado com sucesso!")
    except ServerSelectionTimeoutError:
        print("[⚠️  AVISO] MongoDB indisponível - Banco não funcionará")
        BANCO_DISPONIVEL = False
    except Exception as e:
        print(f"[❌ ERRO] Falha ao conectar ao MongoDB: {e}")
        BANCO_DISPONIVEL = False
else:
    print("[⚠️  AVISO] MONGO_URI vazia - criando banco fake")
    colecao = None

# --- CONFIGURAÇÃO FLASK ---
app_web = Flask(__name__)
app_web.config['JSON_SORT_KEYS'] = False

# --- CONFIGURAÇÃO BOT ---
app_bot = None
if CREDENCIAIS_OK:
    try:
        app_bot = Client(
            "meu_userbot",
            session_string=SESSION_STRING,
            api_id=API_ID,
            api_hash=API_HASH,
            no_updates=False,  # Garante que recebe updates
        )
        print("[✅] Pyrogram configurado com sucesso!")
    except Exception as e:
        print(f"[❌ ERRO] Falha ao configurar Pyrogram: {e}")
        app_bot = None

# Inicializa a lista vazia
PALAVRAS_CHAVE = []
BOT_RODANDO = False

# --- FUNÇÕES DE BANCO DE DADOS ---
def carregar_palavras():
    global BANCO_DISPONIVEL
    
    if not BANCO_DISPONIVEL or not colecao:
        print("[⚠️  AVISO] Usando palavras padrão (banco indisponível)")
        return ['urgente', 'comprar', 'ajuda', 'orçamento']
    
    try:
        dados = colecao.find_one({"id": "lista_principal"})
        if dados:
            return dados['palavras']
        
        # Se não existe, cria com palavras padrão
        padrao = ['urgente', 'comprar', 'ajuda', 'orçamento']
        salvar_palavras(padrao)
        return padrao
    except Exception as e:
        print(f"[ERRO] Falha ao carregar palavras: {e}")
        BANCO_DISPONIVEL = False
        return []

def salvar_palavras(palavras):
    global BANCO_DISPONIVEL
    
    if not BANCO_DISPONIVEL or not colecao:
        print("[⚠️  AVISO] Não foi possível salvar no banco (indisponível)")
        return
    
    try:
        colecao.update_one(
            {"id": "lista_principal"},
            {"$set": {"palavras": palavras}},
            upsert=True
        )
        print(f"[LOG] Palavras salvas no MongoDB: {palavras}")
    except Exception as e:
        print(f"[ERRO] Falha ao salvar palavras: {e}")
        BANCO_DISPONIVEL = False

# --- COMANDOS (group=1 para prioridade) ---
if app_bot:
    @app_bot.on_message(
        filters.command("adicionar", prefixes=["/", ".", "!"]), 
        group=1
    )
    async def comando_adicionar(client, message):
        """Adiciona uma palavra-chave à lista de monitoramento"""
        global PALAVRAS_CHAVE
        
        # Verifica se o comando veio de um chat privado (segurança)
        if not message.chat.type == "private":
            return
        
        texto = message.text.split(" ", 1)
        
        if len(texto) < 2:
            await message.reply_text("⚠️ Digite a palavra após o comando.\n\nEx: `/adicionar pix`")
            return
        
        palavra = texto[1].strip().lower()
        
        if not palavra:
            await message.reply_text("⚠️ A palavra não pode ser vazia!")
            return
        
        if palavra in PALAVRAS_CHAVE:
            await message.reply_text(f"ℹ️ A palavra '{palavra}' já está na lista.")
        else:
            PALAVRAS_CHAVE.append(palavra)
            salvar_palavras(PALAVRAS_CHAVE)
            await message.reply_text(f"✅ Palavra '{palavra}' adicionada com sucesso!")
            print(f"[LOG] Palavra adicionada: {palavra}")

    @app_bot.on_message(
        filters.command("remover", prefixes=["/", ".", "!"]), 
        group=1
    )
    async def comando_remover(client, message):
        """Remove uma palavra-chave da lista de monitoramento"""
        global PALAVRAS_CHAVE
        
        if not message.chat.type == "private":
            return
        
        texto = message.text.split(" ", 1)
        
        if len(texto) < 2:
            await message.reply_text("⚠️ Digite a palavra após o comando.\n\nEx: `/remover pix`")
            return
        
        palavra = texto[1].strip().lower()
        
        if palavra in PALAVRAS_CHAVE:
            PALAVRAS_CHAVE.remove(palavra)
            salvar_palavras(PALAVRAS_CHAVE)
            await message.reply_text(f"🗑️ Palavra '{palavra}' removida com sucesso!")
            print(f"[LOG] Palavra removida: {palavra}")
        else:
            await message.reply_text(f"❌ Palavra '{palavra}' não encontrada na lista.")

    @app_bot.on_message(
        filters.command("listar", prefixes=["/", ".", "!"]), 
        group=1
    )
    async def comando_listar(client, message):
        """Lista todas as palavras-chave monitoradas"""
        print(f"[LOG] Comando /listar recebido do chat ID: {message.chat.id}")
        
        if not PALAVRAS_CHAVE:
            await message.reply_text("📋 A lista de palavras está vazia.")
            return
        
        lista_formatada = "\n".join([f"• {p}" for p in PALAVRAS_CHAVE])
        await message.reply_text(f"📋 **Palavras-chave monitoradas ({len(PALAVRAS_CHAVE)}):**\n\n{lista_formatada}")

    # --- MONITORAMENTO ---
    @app_bot.on_message(
        (filters.group | filters.channel) & ~filters.me & filters.text,
        group=2
    )
    async def verificar_mensagem(client, message):
        """Monitora mensagens em grupos/canais e alerta sobre palavras-chave"""
        if not PALAVRAS_CHAVE:
            return
        
        # Ignora mensagens do próprio MEU_APP_ID
        if message.chat.id == MEU_APP_ID:
            return
        
        texto = message.text.lower()
        
        for palavra in PALAVRAS_CHAVE:
            if palavra.lower() in texto:
                try:
                    chat_title = message.chat.title or "Chat"
                    user_name = message.from_user.first_name if message.from_user else "Anônimo"
                    
                    # Tenta criar link para a mensagem
                    link = ""
                    if message.chat.username:
                        link = f"\n🔗 [Ir para Mensagem](https://t.me/{message.chat.username}/{message.id})"
                    
                    alerta = f"🚨 **'{palavra}'** detectada!\n\n📍 **{chat_title}**\n👤 **{user_name}**\n💬 {message.text}{link}"
                    await client.send_message(MEU_APP_ID, alerta)
                    print(f"[ALERTA] Palavra '{palavra}' detectada em {chat_title}")
                except Exception as e:
                    print(f"[ERRO] Falha ao enviar alerta: {e}")
                
                break

# --- ROTAS WEB ---
@app_web.route('/')
def home(): 
    return "✅ Telegram Keyword Monitor Bot - Online"

@app_web.route('/status')
def status():
    """Retorna status do bot em JSON"""
    return jsonify({
        "status": "online" if BOT_RODANDO else "offline",
        "banco_disponivel": BANCO_DISPONIVEL,
        "palavras_carregadas": len(PALAVRAS_CHAVE),
        "palavras": PALAVRAS_CHAVE,
        "credenciais_ok": CREDENCIAIS_OK
    })

@app_web.route('/health')
def health():
    """Health check para Render"""
    return jsonify({"status": "healthy"}), 200

# --- THREAD PARA RODAR O BOT ---
def executar_bot():
    global BOT_RODANDO
    if not app_bot:
        print("[❌] Bot não configurado. Não é possível iniciar.")
        return
    
    try:
        BOT_RODANDO = True
        print("[LOG] Bot iniciando...")
        app_bot.run()
    except PyrogramConnectionError as e:
        print(f"[ERRO] Falha de conexão com Telegram: {e}")
        BOT_RODANDO = False
    except Exception as e:
        print(f"[ERRO] Exceção inesperada no bot: {e}")
        BOT_RODANDO = False

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 INICIANDO TELEGRAM KEYWORD MONITOR BOT (RENDER)")
    print("="*60 + "\n")
    
    # 1. Inicia o servidor Web (CRÍTICO para Render manter a instância viva)
    print("[1/3] Iniciando servidor Flask...")
    try:
        porta = int(os.environ.get("PORT", 10000))
        print(f"[LOG] Servidor será iniciado na porta {porta}")
        threading.Thread(
            target=lambda: app_web.run(host="0.0.0.0", port=porta, debug=False, use_reloader=False), 
            daemon=False  # Importante: não daemon para Render não matar a app
        ).start()
        time.sleep(2)  # Aguarda servidor iniciar
        print(f"[✅] Servidor Flask rodando na porta {porta}")
    except Exception as e:
        print(f"[❌ ERRO] Falha ao iniciar Flask: {e}")
    
    # 2. Carrega palavras do MongoDB
    print("\n[2/3] Carregando palavras do MongoDB...")
    try:
        PALAVRAS_CHAVE = carregar_palavras()
        print(f"[✅] Palavras carregadas: {PALAVRAS_CHAVE}")
    except Exception as e:
        print(f"[ERRO] Falha ao carregar palavras: {e}")
        PALAVRAS_CHAVE = ['urgente', 'comprar', 'ajuda', 'orçamento']
    
    # 3. Inicia o bot
    print("\n[3/3] Iniciando Pyrogram...")
    if app_bot:
        threading.Thread(target=executar_bot, daemon=False).start()
        print("[✅] Bot iniciado em thread separada")
    else:
        print("[❌] Não foi possível iniciar o bot (credenciais ausentes)")
    
    print("\n" + "="*60)
    print("✅ SISTEMA PRONTO! Flask rodando em background.")
    print("="*60 + "\n")
    
    # Mantém a aplicação rodando
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[LOG] Encerrando aplicação...")