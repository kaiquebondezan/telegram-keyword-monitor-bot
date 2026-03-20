import os
import threading
import asyncio
import time
from flask import Flask, jsonify
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from pyrogram import Client, filters

# --- CREDENCIAIS ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
MONGO_URI = os.environ.get("MONGO_URI")

# ID do grupo onde os comandos são aceitos E os alertas são enviados.
# Para descobrir o ID do seu grupo, encaminhe uma mensagem dele para @userinfobot.
# O valor geralmente é negativo, ex: -1001234567890
GRUPO_ID = int(os.environ.get("GRUPO_ID", 0))

# --- LOCK PARA SEGURANÇA DE THREADS ---
db_lock = threading.Lock()
keywords_lock = threading.Lock()

# --- VALIDAÇÃO DE CREDENCIAIS ---
print("[LOG] Validando credenciais...")
CREDENCIAIS_OK = True
if not API_ID or not API_HASH or not SESSION_STRING:
    print("[ERRO] Alguma credencial do Telegram está vazia!")
    print(f"  API_ID: {bool(API_ID)}")
    print(f"  API_HASH: {bool(API_HASH)}")
    print(f"  SESSION_STRING: {bool(SESSION_STRING)}")
    CREDENCIAIS_OK = False

if not GRUPO_ID:
    print("[ERRO] GRUPO_ID não configurado!")
    CREDENCIAIS_OK = False
else:
    print(f"[OK] Grupo de alertas/comandos: {GRUPO_ID}")

if not MONGO_URI:
    print("[AVISO] MONGO_URI não configurada!")
    CREDENCIAIS_OK = False

# --- CONFIGURAÇÃO MONGODB ---
mongo_client = None
BANCO_DISPONIVEL = False
colecao = None

if MONGO_URI:
    try:
        mongo_client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            retryWrites=False
        )
        mongo_client.admin.command('ping')
        db = mongo_client['monitor_bot_db']
        colecao = db['palavras_chave']
        BANCO_DISPONIVEL = True
        print("[OK] MongoDB conectado!")
    except ServerSelectionTimeoutError:
        print("[AVISO] MongoDB indisponível")
        BANCO_DISPONIVEL = False
    except Exception as e:
        print(f"[ERRO] MongoDB: {e}")
        BANCO_DISPONIVEL = False

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
        print("[OK] Pyrogram configurado!")
    except Exception as e:
        print(f"[ERRO] Pyrogram: {e}")
        app_bot = None

PALAVRAS_CHAVE = []
BOT_RODANDO = False


# --- FUNÇÕES AUXILIARES ---
def é_grupo_autorizado(message) -> bool:
    """Retorna True apenas se o comando veio do grupo configurado em GRUPO_ID."""
    return message.chat.id == GRUPO_ID


def nome_remetente(message) -> str:
    """Retorna o nome do remetente, compatível com canais onde from_user é None."""
    if message.from_user:
        return message.from_user.first_name or "Usuário"
    if message.sender_chat:
        return message.sender_chat.title or "Canal"
    return "Anônimo"


# --- FUNÇÕES DE BANCO DE DADOS ---
def carregar_palavras():
    global BANCO_DISPONIVEL

    if not BANCO_DISPONIVEL or colecao is None:
        print("[AVISO] Usando lista vazia (banco indisponível)")
        return []

    try:
        with db_lock:
            dados = colecao.find_one({"_id": "lista_principal"})
            if dados:
                return dados.get('palavras', [])
        return []
    except Exception as e:
        print(f"[ERRO] Carregar palavras: {e}")
        BANCO_DISPONIVEL = False
        return []


def salvar_palavras(palavras):
    global BANCO_DISPONIVEL

    if not BANCO_DISPONIVEL or colecao is None:
        print("[AVISO] Banco indisponível - não salvo")
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

        # Ignora silenciosamente comandos fora do grupo autorizado
        if not é_grupo_autorizado(message):
            return

        try:
            texto = message.text.split(" ", 1)
            if len(texto) < 2:
                await message.reply_text("Use: /adicionar palavra")
                return

            palavra = texto[1].strip().lower()
            if not palavra or len(palavra) < 2:
                await message.reply_text("Palavra muito curta (mínimo 2 letras)")
                return

            with keywords_lock:
                if palavra in PALAVRAS_CHAVE:
                    await message.reply_text(f"'{palavra}' já existe na lista")
                    return
                PALAVRAS_CHAVE.append(palavra)
                palavras_para_salvar = PALAVRAS_CHAVE.copy()

            salvar_palavras(palavras_para_salvar)
            await message.reply_text(f"✅ '{palavra}' adicionada!")
            print(f"[LOG] +{palavra}")
        except Exception as e:
            print(f"[ERRO] adicionar: {e}")
            await message.reply_text("Erro ao adicionar")

    @app_bot.on_message(filters.command("remover"), group=1)
    async def comando_remover(client, message):
        global PALAVRAS_CHAVE

        if not é_grupo_autorizado(message):
            return

        try:
            texto = message.text.split(" ", 1)
            if len(texto) < 2:
                await message.reply_text("Use: /remover palavra")
                return

            palavra = texto[1].strip().lower()

            with keywords_lock:
                if palavra not in PALAVRAS_CHAVE:
                    await message.reply_text(f"'{palavra}' não está na lista")
                    return
                PALAVRAS_CHAVE.remove(palavra)
                palavras_para_salvar = PALAVRAS_CHAVE.copy()

            salvar_palavras(palavras_para_salvar)
            await message.reply_text(f"🗑️ '{palavra}' removida!")
            print(f"[LOG] -{palavra}")
        except Exception as e:
            print(f"[ERRO] remover: {e}")
            await message.reply_text("Erro ao remover")

    @app_bot.on_message(filters.command("listar"), group=1)
    async def comando_listar(client, message):
        if not é_grupo_autorizado(message):
            return

        print("[LOG] COMANDO /listar RECEBIDO!", flush=True)

        try:
            with keywords_lock:
                if not PALAVRAS_CHAVE:
                    await message.reply_text("📋 Lista vazia")
                    return
                lista = "\n".join([f"• {p}" for p in sorted(PALAVRAS_CHAVE)])
                total = len(PALAVRAS_CHAVE)

            await message.reply_text(f"📋 Monitorando ({total}):\n\n{lista}")
        except Exception as e:
            print(f"[ERRO] listar: {type(e).__name__}: {e}", flush=True)
            import traceback
            traceback.print_exc()

    # --- MONITORAMENTO ---
    # Monitora todos os grupos/canais que o userbot participa,
    # incluindo mensagens do próprio dono da conta
    @app_bot.on_message(
        (filters.group | filters.channel) & filters.text,
        group=2
    )
    async def verificar_mensagem(client, message):
        try:
            with keywords_lock:
                if not PALAVRAS_CHAVE:
                    return
                palavras = PALAVRAS_CHAVE.copy()

            texto = message.text.lower()

            for palavra in palavras:
                if palavra in texto:
                    try:
                        chat_title = message.chat.title or "Chat"
                        user_name = nome_remetente(message)
                        link = (
                            f"\nhttps://t.me/{message.chat.username}/{message.id}"
                            if message.chat.username else ""
                        )
                        alerta = (
                            f"🚨 Palavra detectada: '{palavra}'\n\n"
                            f"📍 {chat_title}\n"
                            f"👤 {user_name}\n"
                            f"💬 {message.text[:200]}"
                            f"{link}"
                        )
                        # Alerta sempre enviado para o grupo fixo configurado em GRUPO_ID
                        await client.send_message(GRUPO_ID, alerta)
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
async def iniciar_bot():
    global BOT_RODANDO
    if not app_bot:
        print("[ERRO] Bot não configurado", flush=True)
        return

    try:
        print("[LOG] Bot conectando ao Telegram...", flush=True)
        await app_bot.start()
        BOT_RODANDO = True
        print("[OK] Bot conectado com sucesso!", flush=True)
        print("[LOG] Bot aguardando mensagens...", flush=True)

        while BOT_RODANDO:
            await asyncio.sleep(1)

    except Exception as e:
        print(f"[ERRO] Bot: {type(e).__name__}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        BOT_RODANDO = False
    finally:
        try:
            if app_bot:
                print("[LOG] Bot desconectando...", flush=True)
                await app_bot.stop()
        except Exception as e:
            print(f"[ERRO] Ao desconectar: {e}", flush=True)
        BOT_RODANDO = False
        print("[LOG] Bot desconectado", flush=True)


def executar_bot():
    """Executa o bot em um novo event loop isolado."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(iniciar_bot())
    except KeyboardInterrupt:
        print("[LOG] Bot interrompido pelo usuário", flush=True)
    finally:
        loop.close()
        print("[LOG] Event loop encerrado", flush=True)


# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TELEGRAM KEYWORD MONITOR BOT")
    print("=" * 60 + "\n")

    # 1. Carregar palavras
    print("[1/3] Carregando palavras...")
    try:
        PALAVRAS_CHAVE = carregar_palavras()
        print(f"[OK] {len(PALAVRAS_CHAVE)} palavras carregadas")
    except Exception as e:
        print(f"[ERRO] {e}")
        PALAVRAS_CHAVE = []

    # 2. Iniciar bot em thread separada
    print("\n[2/3] Iniciando bot...")
    if app_bot:
        # daemon=True: thread encerra junto com o processo principal
        bot_thread = threading.Thread(target=executar_bot, daemon=True)
        bot_thread.start()
        print("[OK] Bot thread iniciada")
        time.sleep(2)
    else:
        print("[ERRO] Credenciais ausentes, bot não iniciado")

    # 3. Iniciar Flask na thread principal
    print("\n[3/3] Iniciando Flask...")
    try:
        porta = int(os.environ.get("PORT", 10000))
        print(f"[OK] Flask iniciando na porta {porta}")
        app_web.run(
            host="0.0.0.0",
            port=porta,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        print(f"[ERRO] Flask: {e}")