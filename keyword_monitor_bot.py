import os
import json
import threading
import asyncio
from flask import Flask
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from pyrogram import Client, filters

# --- CREDENCIAIS ---
# O Render vai puxar essas informações das Variáveis de Ambiente
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")

# Inicializa o servidor Web e o Cliente do Telegram
app_web = Flask(__name__)
app_bot = Client("meu_userbot", session_string=SESSION_STRING, api_id=API_ID, api_hash=API_HASH)

ARQUIVO_PALAVRAS = 'palavras.json'

# --- FUNÇÕES DE SALVAMENTO ---
def carregar_palavras():
    if os.path.exists(ARQUIVO_PALAVRAS):
        with open(ARQUIVO_PALAVRAS, 'r', encoding='utf-8') as f:
            return json.load(f)
    padrao = ['urgente', 'comprar', 'ajuda', 'orçamento']
    salvar_palavras(padrao)
    return padrao

def salvar_palavras(palavras):
    with open(ARQUIVO_PALAVRAS, 'w', encoding='utf-8') as f:
        json.dump(palavras, f, ensure_ascii=False)

PALAVRAS_CHAVE = carregar_palavras()

# --- COMANDOS (Use nas suas Mensagens Salvas) ---
# filters.me garante que o bot só obedeça se VOCÊ enviar o comando
@app_bot.on_message(filters.command("adicionar", prefixes=["/", ".", "!"]) & filters.me)
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
        await message.reply_text(f"✅ Palavra '{palavra}' adicionada com sucesso!")

@app_bot.on_message(filters.command("remover", prefixes=["/", ".", "!"]) & filters.me)
async def comando_remover(client, message):
    global PALAVRAS_CHAVE
    texto = message.text.split(" ", 1)
    
    if len(texto) < 2:
        return
    
    palavra = texto[1].strip().lower()
    if palavra in PALAVRAS_CHAVE:
        PALAVRAS_CHAVE.remove(palavra)
        salvar_palavras(PALAVRAS_CHAVE)
        await message.reply_text(f"🗑️ Palavra '{palavra}' removida!")
    else:
        await message.reply_text(f"A palavra '{palavra}' não foi encontrada.")

@app_bot.on_message(filters.command("listar", prefixes=["/", ".", "!"]) & filters.me)
async def comando_listar(client, message):
    if not PALAVRAS_CHAVE:
        await message.reply_text("Sua lista de palavras está vazia.")
        return
    
    lista_formatada = "\n".join([f"- {p}" for p in PALAVRAS_CHAVE])
    await message.reply_text(f"📋 **Suas palavras-chave:**\n{lista_formatada}")

# --- MONITORAMENTO DE GRUPOS E CANAIS ---
# filters.group e filters.channel olham apenas para grupos e canais
# ~filters.me faz ele ignorar mensagens que você mesmo enviou (evita loop)
@app_bot.on_message((filters.group | filters.channel) & ~filters.me & filters.text)
async def verificar_mensagem(client, message):
    texto = message.text.lower()
    
    for palavra in PALAVRAS_CHAVE:
        if palavra.lower() in texto:
            chat_title = message.chat.title or "Chat Desconhecido"
            user_name = message.from_user.first_name if message.from_user else "Anônimo/Canal"
            
            # Tenta gerar um link direto para a mensagem
            link_msg = ""
            if message.chat.username:
                link_msg = f"\n🔗 [Ir para a Mensagem](https://t.me/{message.chat.username}/{message.id})"
            elif message.link:
                link_msg = f"\n🔗 [Ir para a Mensagem]({message.link})"

            alerta = (
                f"🚨 **Palavra detectada: '{palavra}'**\n\n"
                f"📍 **Local:** {chat_title}\n"
                f"👤 **Enviado por:** {user_name}\n"
                f"💬 **Texto:** {message.text}"
                f"{link_msg}"
            )
            
            # Manda o alerta para as suas Mensagens Salvas ("me")
            await client.send_message("me", alerta)
            break

# --- ROTA WEB (Anti-Sleep do Render) ---
@app_web.route('/')
def home():
    return "O UserBot está rodando e lendo as mensagens!"

def rodar_web():
    porta = int(os.environ.get("PORT", 5000))
    # use_reloader=False é vital aqui para não rodar dois bots e dar conflito
    app_web.run(host="0.0.0.0", port=porta, use_reloader=False)

if __name__ == "__main__":
    # Inicia o servidor web em paralelo
    threading.Thread(target=rodar_web, daemon=True).start()
    
    # Inicia o UserBot do Telegram
    print("Iniciando o UserBot...")
    app_bot.run()