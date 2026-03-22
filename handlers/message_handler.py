import logging

from pyrogram import Client, filters
from pyrogram.types import Message

import database.mongodb as db
from config import CONTROL_GROUP_ID

logger = logging.getLogger(__name__)


def not_control_group(client, filter_obj, message: Message) -> bool:
    return message.chat and message.chat.id != CONTROL_GROUP_ID


_external_filter = filters.create(not_control_group)


def _format_alert(keyword: str, message: Message) -> str:
    chat_name = getattr(message.chat, "title", None) or getattr(message.chat, "username", None) or str(message.chat.id)
    sender_name = ""
    if message.from_user:
        sender_name = message.from_user.first_name or ""
        if message.from_user.last_name:
            sender_name += f" {message.from_user.last_name}"
        if message.from_user.username:
            sender_name += f" (@{message.from_user.username})"
    elif message.sender_chat:
        sender_name = getattr(message.sender_chat, "title", str(message.sender_chat.id))

    text = message.text or message.caption or ""
    snippet = text if len(text) <= 300 else text[:300] + "…"
    date_str = message.date.strftime("%d/%m/%Y %H:%M") if message.date else ""

    lines = [
        f"🔔 *Keyword detectada:* {keyword}",
        f"📍 *Chat:* {chat_name}",
    ]
    if sender_name:
        lines.append(f"👤 *De:* {sender_name}")
    if date_str:
        lines.append(f"🕐 {date_str}")
    lines.append(f"\n_{snippet}_")
    lines.append(f"\n[Ver mensagem original]({message.link})")  # Link clicável
    return "\n".join(lines)


def register(app: Client) -> None:
    @app.on_message(_external_filter & (filters.text | filters.caption))
    async def monitor_messages(client: Client, message: Message) -> None:
        keywords = await db.get_keywords()
        if not keywords:
            return

        text = (message.text or message.caption or "").lower()
        if not text:
            return

        matched = [kw for kw in keywords if kw in text]
        if not matched:
            return

        chat_name = getattr(message.chat, "title", None) or str(message.chat.id)
        logger.info(
            "Match encontrado em '%s': keywords=%s",
            chat_name,
            matched,
        )

        for keyword in matched:
            alert = _format_alert(keyword, message)
            try:
                await client.send_message(CONTROL_GROUP_ID, alert)
            except Exception as e:
                logger.error(
                    "Falha ao enviar alerta para o grupo de controle (keyword='%s'): %s",
                    keyword,
                    e,
                )