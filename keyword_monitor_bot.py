import os
import json
import threading
import asyncio
import time
from flask import Flask, jsonify
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

# --- CONFIGURAÇÃO DE EVENT LOOP PARA RENDER ---
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from pyrogram import Client, filters
# from pyrogram.errors import ConnectionError as PyrogramConnectionError

# --- CREDENCIAIS ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
MEU_APP_ID = int(os.environ.get("MEU_APP_ID", 0))
MONGO_URI = os.environ.get("MONGO_URI")

# --- LOCK PARA SEGURANÇA DE THREADS ---
db_lock = threading.Lock()
keywords_lock = threading.Lock()

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
    print("[⚠️  AVISO] MONGO_URI não configurada!")
    CREDENCIAIS_OK = False

# --- CONFIGURAÇÃO MONGODB ---
mongo_client = None
BANCO_DISPONIVEL = False

if MONGO_URI:
    try:
        mongo_client = MongoClient(MONGO_URI, 
                                  serverSelectionTimeoutMS=5000, 
                                  connectTimeoutMS=5000,
                                  retryWrites=False)
        mongo_client.admin.command('ping')
        db = mongo_client['monitor_bot_db']
        colecao = db['palavras_chave']
        BANCO_DISPONIVEL = True
        print("[✅] MongoDB conectado!")
    except ServerSelectionTimeoutError:
        print("[⚠️  AVISO] MongoDB indisponível")
        BANCO_DISPONIVEL = False
    except Exception as e:
        print(f"[❌ ERRO] MongoDB: {e}")
        BANCO_DISPONIVEL = False
else:
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
            no_updates=False,
        )
        print("[✅] Pyrogram configurado!")
    except Exception as e:
        print(f"[❌ ERRO] Pyrogram: {e}")
        app_bot = None

PALAVRAS_CHAVE = []
BOT_RODANDO = False

# --- FUNÇÕES DE BANCO DE DADOS COM LOCK ---
def carregar_palavras():
    global BANCO_DISPONIVEL
    
    if not BANCO_DISPONIVEL or not colecao:
        print("[⚠️  AVISO] Usando lista vazia (banco indisponível)")
        return []
    
    try:
        with db_lock:
            dados = colecao.find_one({"_id": "lista_principal"})
            if dados:
                return dados.get('palavras', [])
        
        # Se não existe no banco, retorna lista vazia
        return []
    except Exception as e:
        print(f"[ERRO] Carregar palavras: {e}")
        BANCO_DISPONIVEL = False
        return []

def salvar_palavras(palavras):
    global BANCO_DISPONIVEL
    
    if not BANCO_DISPONIVEL or not colecao:
        print("[⚠️  AVISO] Banco indisponível - não salvo")
        return
    
    try:
        with db_lock:
            colecao.update_one(
                {"_id": "lista_principal"},
                {"$set": {"palavras": palavras}},
                upsert=True
            )
        print(f"[LOG] {len(palavras)} palavras salvas")
    except Exception as e:
        print(f"[ERRO] Salvar palavras: {e}")
        BANCO_DISPONIVEL = False

# --- COMANDOS ---
if app_bot:
    @app_bot.on_message(filters.command("adicionar"), group=1)
    async def comando_adicionar(client, message):
        global PALAVRAS_CHAVE
        
        if message.chat.type != "private":
            return
        
        try:
            texto = message.text.split(" ", 1)
            if len(texto) < 2:
                await message.reply_text("⚠️ Use: `/adicionar palavra`")
                return
            
            palavra = texto[1].strip().lower()
            if not palavra or len(palavra) < 2:
                await message.reply_text("⚠️ Palavra muito curta (mínimo 2 letras)")
                return
            
            with keywords_lock:
                if palavra in PALAVRAS_CHAVE:
                    await message.reply_text(f"ℹ️ '{palavra}' já existe")
                    return
                
                PALAVRAS_CHAVE.append(palavra)
            
            salvar_palavras(PALAVRAS_CHAVE)
            await message.reply_text(f"✅ '{palavra}' adicionada!")
            print(f"[LOG] +{palavra}")
        except Exception as e:
            print(f"[ERRO] adicionar: {e}")
            await message.reply_text("❌ Erro ao adicionar")

    @app_bot.on_message(filters.command("remover"), group=1)
    async def comando_remover(client, message):
        global PALAVRAS_CHAVE
        
        if message.chat.type != "private":
            return
        
        try:
            texto = message.text.split(" ", 1)
            if len(texto) < 2:
                await message.reply_text("⚠️ Use: `/remover palavra`")
                return
            
            palavra = texto[1].strip().lower()
            
            with keywords_lock:
                if palavra in PALAVRAS_CHAVE:
                    PALAVRAS_CHAVE.remove(palavra)
                else:
                    await message.reply_text(f"❌ '{palavra}' não existe")
                    return
            
            salvar_palavras(PALAVRAS_CHAVE)
            await message.reply_text(f"🗑️ '{palavra}' removida!")
            print(f"[LOG] -{palavra}")
        except Exception as e:
            print(f"[ERRO] remover: {e}")
            await message.reply_text("❌ Erro ao remover")

    @app_bot.on_message(filters.command("listar"), group=1)
    async def comando_listar(client, message):
        if message.chat.type != "private":
            return
        
        try:
            with keywords_lock:
                if not PALAVRAS_CHAVE:
                    await message.reply_text("📋 Lista vazia")
                    return
                
                lista = "\n".join([f"• {p}" for p in sorted(PALAVRAS_CHAVE)])
            
            await message.reply_text(f"📋 Monitorando ({len(PALAVRAS_CHAVE)}):\n\n{lista}")
        except Exception as e:
            print(f"[ERRO] listar: {e}")

    # --- MONITORAMENTO ---
    @app_bot.on_message(
        (filters.group | filters.channel) & ~filters.me & filters.text,
        group=2
    )
    async def verificar_mensagem(client, message):
        try:
            with keywords_lock:
                if not PALAVRAS_CHAVE:
                    return
                palavras = PALAVRAS_CHAVE.copy()
            
            if message.chat.id == MEU_APP_ID:
                return
            
            texto = message.text.lower()
            
            for palavra in palavras:
                if palavra in texto:
                    try:
                        chat_title = message.chat.title or "Chat"
                        user_name = message.from_user.first_name if message.from_user else "Anônimo"
                        link = f"\nhttps://t.me/{message.chat.username}/{message.id}" if message.chat.username else ""
                        
                        alerta = f"🚨 **'{palavra}'** detectada!\n\n📍 {chat_title}\n👤 {user_name}\n💬 {message.text[:100]}{link}"
                        await client.send_message(MEU_APP_ID, alerta)
                        print(f"[ALERTA] '{palavra}' em {chat_title}")
                    except Exception as e:
                        print(f"[ERRO] enviar alerta: {e}")
                    break
        except Exception as e:
            print(f"[ERRO] verificar_mensagem: {e}")

# --- ROTAS WEB ---
@app_web.route('/')
def home():
    return "✅ Online"

@app_web.route('/status')
def status():
    with keywords_lock:
        num_palavras = len(PALAVRAS_CHAVE)
        palavras = PALAVRAS_CHAVE.copy()
    
    return jsonify({
        "status": "online" if BOT_RODANDO else "offline",
        "banco_disponivel": BANCO_DISPONIVEL,
        "palavras_carregadas": num_palavras,
        "palavras": palavras
    })

@app_web.route('/health')
def health():
    return jsonify({"status": "healthy", "bot": "online" if BOT_RODANDO else "offline"}), 200

# --- BOT RUNNER ---
def executar_bot():
    global BOT_RODANDO
    if not app_bot:
        print("[❌] Bot não configurado")
        return
    
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            BOT_RODANDO = True
            print("[LOG] Bot iniciando...")
            app_bot.run()
        except Exception as e:
            print(f"[ERRO] Falha de conexão: {e}")
            BOT_RODANDO = False
            retry_count += 1
            if retry_count < max_retries:
                print(f"[LOG] Tentando reconectar ({retry_count}/{max_retries})...")
                time.sleep(5)
    
    BOT_RODANDO = False
    print("[❌] Bot desconectado após retries")

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 TELEGRAM KEYWORD MONITOR BOT")
    print("="*60 + "\n")
    
    # 1. Flask
    print("[1/3] Iniciando Flask...")
    try:
        porta = int(os.environ.get("PORT", 10000))
        threading.Thread(
            target=lambda: app_web.run(host="0.0.0.0", port=porta, debug=False, use_reloader=False),
            daemon=False
        ).start()
        time.sleep(2)
        print(f"[✅] Flask porta {porta}")
    except Exception as e:
        print(f"[❌] Flask: {e}")
    
    # 2. Carregar palavras
    print("\n[2/3] Carregando palavras...")
    try:
        PALAVRAS_CHAVE = carregar_palavras()
        print(f"[✅] {len(PALAVRAS_CHAVE)} palavras carregadas")
    except Exception as e:
        print(f"[ERRO] {e}")
        PALAVRAS_CHAVE = []
    
    # 3. Bot
    print("\n[3/3] Iniciando bot...")
    if app_bot:
        threading.Thread(target=executar_bot, daemon=False).start()
        print("[✅] Bot thread iniciada")
    else:
        print("[❌] Credenciais ausentes")
    
    print("\n" + "="*60)
    print("✅ Sistema pronto!")
    print("="*60 + "\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[LOG] Encerrando...")
        BOT_RODANDO = False