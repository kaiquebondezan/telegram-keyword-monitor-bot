import logging
from datetime import timezone, timedelta

from telethon import TelegramClient, events

import database.mongodb as db
from config import CONTROL_GROUP_ID

logger = logging.getLogger(__name__)
BRT = timezone(timedelta(hours=-3))


def register(client: TelegramClient) -> None:
    @client.on(events.NewMessage(incoming=True))
    async def handle_message(event):
        # Ignora o grupo de controle
        if event.chat_id == CONTROL_GROUP_ID:
            return

        # Ignora mensagens sem texto
        if not event.message.text:
            return

        chat_name = event.chat.title if hasattr(event.chat, 'title') else str(event.chat_id)
        text = event.message.text.lower()

        keywords = await db.get_keywords()
        if not keywords:
            return

        matched = [kw for kw in keywords if kw in text]
        if not matched:
            logger.debug(f"Nenhuma keyword correspondida em '{chat_name}'")
            return

        logger.info("Match encontrado em '%s': keywords=%s", chat_name, matched)

        for keyword in matched:
            try:
                # Forward da mensagem
                await client.forward_messages(CONTROL_GROUP_ID, event.message)

                # Coleta informações do sender
                sender_name = ""
                if event.message.from_id:
                    sender = await client.get_entity(event.message.from_id)
                    sender_name = sender.first_name or ""
                    if hasattr(sender, 'last_name') and sender.last_name:
                        sender_name += f" {sender.last_name}"
                    if hasattr(sender, 'username') and sender.username:
                        sender_name += f" (@{sender.username})"

                date_str = event.message.date.astimezone(BRT).strftime("%d/%m/%Y %H:%M")

                alert = f"🔔 Palavra detectada: {keyword}\n📍 Chat: {chat_name}"
                if sender_name:
                    alert += f"\n👤 De: {sender_name}"
                alert += f"\n🕐 {date_str}"

                await client.send_message(CONTROL_GROUP_ID, alert)

            except Exception as e:
                logger.error("Falha ao enviar alerta (keyword='%s'): %s", keyword, e)