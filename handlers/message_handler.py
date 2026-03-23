import logging
from datetime import timezone, timedelta

from pyrogram import Client, filters
from pyrogram.types import Message

import database.mongodb as db
from config import CONTROL_GROUP_ID

logger = logging.getLogger(__name__)
BRT = timezone(timedelta(hours=-3))


def not_control_group(client, filter_obj, message: Message) -> bool:
    return message.chat and message.chat.id != CONTROL_GROUP_ID


_external_filter = filters.create(not_control_group)


def register(app: Client) -> None:

    async def process_message(client: Client, message: Message) -> None:
        chat_name = getattr(message.chat, "title", None) or getattr(message.chat, "username", None) or str(message.chat.id)
        text_preview = (message.text or message.caption or "")[:50]
        logger.info(f"[DEBUG] Processando em '{chat_name}': {text_preview}")
        
        keywords = await db.get_keywords()
        if not keywords:
            logger.info(f"[DEBUG] Nenhuma keyword cadastrada")
            return

        text = (message.text or message.caption or "").lower()
        if not text:
            logger.info(f"[DEBUG] Mensagem vazia ou sem texto")
            return

        matched = [kw for kw in keywords if kw in text]
        if not matched:
            logger.info(f"[DEBUG] Nenhuma keyword correspondida. Keywords: {keywords}, Texto: {text[:100]}")
            return

        logger.info("Match encontrado em '%s': keywords=%s", chat_name, matched)

        for keyword in matched:
            try:
                await client.forward_messages(
                    chat_id=CONTROL_GROUP_ID,
                    from_chat_id=message.chat.id,
                    message_ids=message.id
                )

                sender_name = ""
                if message.from_user:
                    sender_name = message.from_user.first_name or ""
                    if message.from_user.last_name:
                        sender_name += f" {message.from_user.last_name}"
                    if message.from_user.username:
                        sender_name += f" (@{message.from_user.username})"
                elif message.sender_chat:
                    sender_name = getattr(message.sender_chat, "title", str(message.sender_chat.id))

                date_str = message.date.astimezone(BRT).strftime("%d/%m/%Y %H:%M") if message.date else ""

                alert = f"🔔 Palavra detectada: {keyword}\n📍 Chat: {chat_name}"
                if sender_name:
                    alert += f"\n👤 De: {sender_name}"
                if date_str:
                    alert += f"\n🕐 {date_str}"
                await client.send_message(CONTROL_GROUP_ID, alert)

            except Exception as e:
                logger.error("Falha ao enviar alerta (keyword='%s'): %s", keyword, e)

    # Captura TUDO - sem filtros
    @app.on_message()
    async def catch_all(client: Client, message: Message) -> None:
        # Ignora o grupo de controle
        if message.chat.id == CONTROL_GROUP_ID:
            return
            
        chat_name = getattr(message.chat, "title", None) or getattr(message.chat, "username", None) or str(message.chat.id)
        has_text = bool(message.text or message.caption)
        msg_type = type(message).__name__
        
        logger.info(f"[CATCH ALL] Chat: {chat_name} (ID: {message.chat.id}) | Tipo: {msg_type} | Tem texto: {has_text}")
        
        # Se tem texto/caption, processa
        if has_text:
            await process_message(client, message)

    logger.info("[INIT] Message handler com catch-all ativo")