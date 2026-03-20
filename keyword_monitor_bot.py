import os
import json
import threading
import asyncio
from flask import Flask
from pymongo import MongoClient

# --- CORREÇÃO PARA O PYTHON NO RENDER ---
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from pyrogram import Client, filters

# --- CREDENCIAIS ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
MEU_APP_ID = int(os.environ.get("MEU_APP_ID", 0))
MONGO_URI = os.environ.get("MONGO_URI")

# --- VALIDAÇÃO DE CREDENCIAIS ---
print("[LOG] Validando credenciais...")
if not API_ID or not API_HASH or not SESSION_STRING or not MEU_APP_ID:
    print("[AVISO] Alguma credencial do Telegram está vazia!")
    print(f"  API_ID: {bool(API_ID)}")
    print(f"  API_HASH: {bool(API_HASH)}")
    print(f"  SESSION_STRING: {bool(SESSION_STRING)}")
    print(f"  MEU_APP_ID: {bool(MEU_APP_ID)}")

if not MONGO_URI:
    print("[AVISO] MONGO_URI não configurada! Banco de dados pode não funcionar.")

# --- CONFIGURAÇÃO MONGODB (Com Timeout de Segurança) ---
mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = mongo_client['monitor_bot_db']
colecao = db['palavras_chave']

app_web = Flask(__name__)
app_bot = Client("meu_userbot", session_string=SESSION_STRING, api_id=API_ID, api_hash=API_HASH)

# Inicializa a lista vazia
PALAVRAS_CHAVE = []
BANCO_DISPONIVEL = False

# --- FUNÇÕES DE BANCO DE DADOS ---
def carregar_palavras():
    global BANCO_DISPONIVEL
    try:
        dados = colecao.find_one({"id": "lista_principal"})
        if dados:
            BANCO_DISPONIVEL = True
            return dados['palavras']
        
        # Se não existe, cria com palavras padrão
        padrao = ['urgente', 'comprar', 'ajuda', 'orçamento']
        salvar_palavras(padrao)
        BANCO_DISPONIVEL = True
        return padrao
    except Exception as e:
        print(f"[ERRO] Falha ao carregar palavras: {e}")
        BANCO_DISPONIVEL = False
        return []

def salvar_palavras(palavras):
    global BANCO_DISPONIVEL
    try:
        colecao.update_one(
            {"id": "lista_principal"},
            {"$set": {"palavras": palavras}},
            upsert=True
        )
        BANCO_DISPONIVEL = True
        print(f"[LOG] Palavras salvas no MongoDB: {palavras}")
    except Exception as e:
        print(f"[ERRO] Falha ao salvar palavras: {e}")
        BANCO_DISPONIVEL = False

# --- COMANDOS (group=1 para prioridade) ---
@app_bot.on_message(
    filters.command("adicionar", prefixes=["/", ".", "!"]), 
    group=1
)
async def comando_adicionar(client, message):
    """Adiciona uma palavra-chave à lista de monitoramento"""
    global PALAVRAS_CHAVE
    
    # Verifica se o comando veio de um chat privado (segurança)
    if not message.chat.type == "private":
        print(f"[LOG] Comando /adicionar recebido de um grupo/canal. Ignorando.")
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
    
    # Verifica se o comando veio de um chat privado (segurança)
    if not message.chat.type == "private":
        print(f"[LOG] Comando /remover recebido de um grupo/canal. Ignorando.")
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
    
    if not BANCO_DISPONIVEL:
        await message.reply_text("⚠️ Banco de dados indisponível no momento!")
        return
    
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
    if not PALAVRAS_CHAVE or not BANCO_DISPONIVEL:
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
            
            break  # Para na primeira palavra detectada

# --- ROTA WEB ---
@app_web.route('/')
def home(): 
    return "✅ UserBot ativo!"

@app_web.route('/status')
def status():
    """Retorna status do bot"""
    return {
        "status": "online",
        "banco_disponivel": BANCO_DISPONIVEL,
        "palavras_carregadas": len(PALAVRAS_CHAVE),
        "palavras": PALAVRAS_CHAVE
    }

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    print("\n" + "="*50)
    print("🤖 INICIANDO TELEGRAM KEYWORD MONITOR BOT")
    print("="*50 + "\n")
    
    # 1. Inicia o servidor Web (Render aprova o Deploy aqui)
    print("[1/3] Iniciando servidor Flask...")
    try:
        porta = int(os.environ.get("PORT", 10000))
        threading.Thread(
            target=lambda: app_web.run(host="0.0.0.0", port=porta, use_reloader=False), 
            daemon=True
        ).start()
        print(f"[OK] Servidor Flask rodando na porta {porta}")
    except Exception as e:
        print(f"[ERRO] Falha ao iniciar Flask: {e}")
    
    # 2. Carrega palavras do MongoDB
    print("\n[2/3] Conectando ao MongoDB...")
    try:
        PALAVRAS_CHAVE = carregar_palavras()
        if BANCO_DISPONIVEL:
            print(f"[OK] Banco conectado! Palavras carregadas: {PALAVRAS_CHAVE}")
        else:
            print("[AVISO] Banco podem estar indisponível. Bot rodará sem persistência.")
    except Exception as e:
        print(f"[ERRO] Falha ao conectar ao MongoDB: {e}")
        BANCO_DISPONIVEL = False
    
    # 3. Inicia o bot
    print("\n[3/3] Iniciando Pyrogram...")
    try:
        app_bot.run()
    except Exception as e:
        print(f"[ERRO] Falha ao iniciar o bot: {e}")