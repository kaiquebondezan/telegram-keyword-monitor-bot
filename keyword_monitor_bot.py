import telebot
from flask import Flask
import threading
import os

TOKEN = os.environ.get('TELEGRAM_TOKEN')
MEU_CHAT_ID = os.environ.get('MEU_CHAT_ID')
PALAVRAS_CHAVE = ['urgente', 'comprar', 'ajuda', 'orçamento']

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "O Bot está rodando e monitorando!"

@bot.message_handler(func=lambda message: True, content_types=['text'])
def verificar_mensagem_grupo(message):
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

def rodar_bot():
    print("Iniciando o polling do Telegram...")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    thread_bot = threading.Thread(target=rodar_bot)
    thread_bot.start()
    
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta)