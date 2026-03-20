import telebot
from flask import Flask
import threading
import os
import json

# --- CONFIGURAÇÕES DO BOT ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
MEU_CHAT_ID = os.environ.get('MEU_CHAT_ID')

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

ARQUIVO_PALAVRAS = 'palavras.json'

# --- FUNÇÕES DE SALVAMENTO ---
def carregar_palavras():
    if os.path.exists(ARQUIVO_PALAVRAS):
        with open(ARQUIVO_PALAVRAS, 'r', encoding='utf-8') as f:
            return json.load(f)
    # Se o arquivo não existir, cria com uma lista padrão
    padrao = ['urgente', 'comprar', 'ajuda', 'orçamento']
    salvar_palavras(padrao)
    return padrao

def salvar_palavras(palavras):
    with open(ARQUIVO_PALAVRAS, 'w', encoding='utf-8') as f:
        json.dump(palavras, f, ensure_ascii=False)

# Carrega as palavras ao iniciar o bot
PALAVRAS_CHAVE = carregar_palavras()

# --- FILTRO DE SEGURANÇA ---
def eh_meu_chefe(message):
    # Só permite que comandos funcionem se vierem do seu Chat ID
    return str(message.chat.id) == str(MEU_CHAT_ID)

# --- COMANDOS DO BOT (SÓ PARA VOCÊ) ---
@bot.message_handler(commands=['adicionar'], func=eh_meu_chefe)
def comando_adicionar(message):
    global PALAVRAS_CHAVE
    texto = message.text.replace('/adicionar', '').strip().lower()
    
    if not texto:
        bot.reply_to(message, "⚠️ Digite a palavra após o comando. Exemplo: `/adicionar pix`", parse_mode='Markdown')
        return
    
    if texto in PALAVRAS_CHAVE:
        bot.reply_to(message, f"A palavra '{texto}' já está na lista.")
    else:
        PALAVRAS_CHAVE.append(texto)
        salvar_palavras(PALAVRAS_CHAVE)
        bot.reply_to(message, f"✅ Palavra '{texto}' adicionada com sucesso!")

@bot.message_handler(commands=['remover'], func=eh_meu_chefe)
def comando_remover(message):
    global PALAVRAS_CHAVE
    texto = message.text.replace('/remover', '').strip().lower()
    
    if texto in PALAVRAS_CHAVE:
        PALAVRAS_CHAVE.remove(texto)
        salvar_palavras(PALAVRAS_CHAVE)
        bot.reply_to(message, f"🗑️ Palavra '{texto}' removida com sucesso!")
    else:
        bot.reply_to(message, f"A palavra '{texto}' não foi encontrada na lista.")

@bot.message_handler(commands=['listar'], func=eh_meu_chefe)
def comando_listar(message):
    if not PALAVRAS_CHAVE:
        bot.reply_to(message, "A lista de palavras-chave está vazia.")
        return
    
    lista_formatada = "\n".join([f"- {p}" for p in PALAVRAS_CHAVE])
    bot.reply_to(message, f"📋 *Suas palavras-chave ativas:*\n{lista_formatada}", parse_mode='Markdown')

# --- ROTA WEB (Para manter o Render feliz) ---
@app.route('/')
def home():
    return "O Bot está rodando e monitorando!"

# --- FUNÇÕES DE MONITORAMENTO ---
@bot.message_handler(func=lambda message: True, content_types=['text'])
def verificar_mensagem_grupo(message):
    # Ignora mensagens privadas para não acionar alertas com os seus próprios comandos
    if message.chat.type == 'private':
        return
        
    texto = message.text.lower()
    for palavra in PALAVRAS_CHAVE:
        if palavra.lower() in texto:
            alerta = f"🚨 *Palavra-chave: '{palavra}'*\n\n📍 *Local:* {message.chat.title}\n👤 *Usuário:* {message.from_user.first_name}\n💬 *Mensagem:* {message.text}"
            bot.send_message(MEU_CHAT_ID, alerta, parse_mode='Markdown')
            break

@bot.channel_post_handler(func=lambda message: True, content_types=['text'])
def verificar_mensagem_canal(message):
    texto = message.text.lower()
    for palavra in PALAVRAS_CHAVE:
        if palavra.lower() in texto:
            alerta = f"🚨 *Palavra-chave: '{palavra}'*\n\n📢 *Canal:* {message.chat.title}\n💬 *Mensagem:* {message.text}"
            bot.send_message(MEU_CHAT_ID, alerta, parse_mode='Markdown')
            break

# --- INICIALIZAÇÃO EM PARALELO ---
def rodar_bot():
    print("Iniciando o polling do Telegram...")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    thread_bot = threading.Thread(target=rodar_bot)
    thread_bot.start()
    
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta)