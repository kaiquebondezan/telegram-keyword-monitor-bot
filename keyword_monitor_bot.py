import os
import json
import threading
import asyncio
from flask import Flask
from pymongo import MongoClient
from pyrogram import Client, filters

# --- CORREÇÃO PARA O PYTHON NO RENDER ---
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# --- CREDENCIAIS ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
MEU_APP_ID = int(os.environ.get("MEU_APP_ID", 0))
MONGO_URI = os.environ.get("MONGO_URI")

# --- CONFIGURAÇÃO MONGODB (Com Timeout de Segurança) ---
# Se o banco não responder em 5 segundos, ele avisa em vez de travar o Render
mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = mongo_client['monitor_bot_db']
colecao = db['palavras_chave']

app_web = Flask(__name__)
app_bot = Client("meu_userbot", session_string=SESSION_STRING, api_id=API_ID, api_hash=API_HASH)

# Inicializa a lista vazia primeiro para não travar o carregamento
PALAVRAS_CHAVE = []

# --- FUNÇÕES DE BANCO DE DADOS ---
def carregar_palavras():
    dados = colecao.find_one({"id": "lista_principal"})
    if dados:
        return dados['palavras']
    
    padrao = ['urgente', 'comprar', 'ajuda', 'orçamento']
    salvar_palavras(padrao)
    return padrao

def salvar_palavras(palavras):
    colecao.update_one(
        {"id": "lista_principal"},
        {"$set": {"palavras": palavras}},
        upsert=True
    )

# --- COMANDOS ---
@app_bot.on_message(filters.command("adicionar", prefixes=["/", ".", "!"]) & filters.chat(MEU_APP_ID))
async def comando_adicionar(client, message):
    global PALAVRAS_CHAVE
    texto = message.text.split(" ", 1)
    
    if len(texto) < 2:
        await message.reply_text("⚠️ Digite a palavra após o comando. Ex: `/adicionar pix`")
        return
    
    palavra = texto[1].strip().lower()
    if palavra in PALAVRAS_CHAVE:
        await message.reply_text(f"A palavra '{palavra}' já está na lista.")
    else:
        PALAVRAS_CHAVE.append(palavra)
        salvar_palavras(PALAVRAS_CHAVE)
        await message.reply_text(f"✅ Palavra '{palavra}' salva no Banco de Dados!")

@app_bot.on_message(filters.command("remover", prefixes=["/", ".", "!"]) & filters.chat(MEU_APP_ID))
async def comando_remover(client, message):
    global PALAVRAS_CHAVE
    texto = message.text.split(" ", 1)
    
    if len(texto) < 2: return
    
    palavra = texto[1].strip().lower()
    if palavra in PALAVRAS_CHAVE:
        PALAVRAS_CHAVE.remove(palavra)
        salvar_palavras(PALAVRAS_CHAVE)
        await message.reply_text(f"🗑️ Palavra '{palavra}' removida do banco!")
    else:
        await message.reply_text("Palavra não encontrada.")

# Trava removida temporariamente para teste
@app_bot.on_message(filters.command("listar", prefixes=["/", ".", "!"]))
async def comando_listar(client, message):
    print(f"[LOG] Comando /listar recebido do chat ID: {message.chat.id}")
    if not PALAVRAS_CHAVE:
        await message.reply_text("Lista vazia ou banco desconectado.")
        return
    lista_formatada = "\n".join([f"- {p}" for p in PALAVRAS_CHAVE])
    await message.reply_text(f"📋 **Palavras no MongoDB:**\n{lista_formatada}")

# --- MONITORAMENTO ---
@app_bot.on_message((filters.group | filters.channel) & ~filters.me & ~filters.chat(MEU_APP_ID) & filters.text)
async def verificar_mensagem(client, message):
    texto = message.text.lower()
    for palavra in PALAVRAS_CHAVE:
        if palavra.lower() in texto:
            chat_title = message.chat.title or "Chat"
            user_name = message.from_user.first_name if message.from_user else "Anônimo"
            link = f"\n🔗 [Ir para Mensagem](https://t.me/{message.chat.username}/{message.id})" if message.chat.username else ""
            
            alerta = f"🚨 **'{palavra}' detectada!**\n\n📍 **{chat_title}**\n👤 **{user_name}**\n💬 {message.text}{link}"
            await client.send_message(MEU_APP_ID, alerta)
            break

# --- ROTA WEB E INICIALIZAÇÃO SEGURA ---
@app_web.route('/')
def home(): 
    return "UserBot ativo!"

if __name__ == "__main__":
    # 1. Liga o servidor Web primeiro (Render aprova o Deploy aqui)
    print("[LOG] Iniciando servidor Flask...")
    porta = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app_web.run(host="0.0.0.0", port=porta, use_reloader=False), daemon=True).start()
    
    # 2. Tenta conectar no MongoDB com segurança
    print("[LOG] Conectando ao MongoDB...")
    try:
        PALAVRAS_CHAVE = carregar_palavras()
        print(f"[LOG] Banco OK! Palavras carregadas: {PALAVRAS_CHAVE}")
    except Exception as e:
        print(f"\n[ERRO CRÍTICO MONGODB] Não foi possível conectar ao banco de dados!\nMotivo: {e}\n")
    
    # 3. Liga o bot
    print("[LOG] Iniciando Pyrogram...")
    app_bot.run()