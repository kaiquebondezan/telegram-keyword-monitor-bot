import logging

from pyrogram import Client, filters
from pyrogram.types import Message

import database.mongodb as db
from config import CONTROL_GROUP_ID

logger = logging.getLogger(_name_)


def in_control_group(, __, message: Message) -> bool:
    return message.chat and message.chat.id == CONTROL_GROUP_ID


_control_group_filter = filters.create(_in_control_group)


def register(app: Client) -> None:
    @app.on_message(_control_group_filter & filters.command("listar"))
    async def cmd_listar(client: Client, message: Message) -> None:
        logger.info("Comando /listar recebido.")
        keywords = await db.get_keywords()
        if not keywords:
            await message.reply("Nenhuma palavra-chave cadastrada.")
            return
        lista = "\n".join(f"• {kw}" for kw in sorted(keywords))
        await message.reply(f"*Palavras-chave monitoradas ({len(keywords)}):*\n\n{lista}")

    @app.on_message(_control_group_filter & filters.command("adicionar"))
    async def cmd_adicionar(client: Client, message: Message) -> None:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            await message.reply("Uso: /adicionar <palavra>")
            return
        keyword = parts[1].strip()
        logger.info("Comando /adicionar: '%s'", keyword)
        inserted = await db.add_keyword(keyword)
        if inserted:
            await message.reply(f"✅ Palavra-chave {keyword.lower()} adicionada.")
        else:
            await message.reply(f"⚠️ A palavra-chave {keyword.lower()} já está cadastrada.")

    @app.on_message(_control_group_filter & filters.command("remover"))
    async def cmd_remover(client: Client, message: Message) -> None:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            await message.reply("Uso: /remover <palavra>")
            return
        keyword = parts[1].strip()
        logger.info("Comando /remover: '%s'", keyword)
        deleted = await db.remove_keyword(keyword)
        if deleted:
            await message.reply(f"🗑️ Palavra-chave {keyword.lower()} removida.")
        else:
            await message.reply(f"❌ Palavra-chave {keyword.lower()} não encontrada.")

    @app.on_message(_control_group_filter & filters.command("ajuda"))
    async def cmd_ajuda(client: Client, message: Message) -> None:
        logger.info("Comando /ajuda recebido.")
        await message.reply(
            "*Comandos disponíveis:*\n\n"
            "/listar — lista todas as palavras-chave monitoradas\n"
            "/adicionar <palavra> — adiciona uma palavra-chave\n"
            "/remover <palavra> — remove uma palavra-chave\n"
            "/ajuda — mostra esta mensagem"
        )