import logging

from telethon import TelegramClient, events

import database.mongodb as db
from config import CONTROL_GROUP_ID

logger = logging.getLogger(__name__)


def register(client: TelegramClient) -> None:
    @client.on(events.NewMessage(chats=CONTROL_GROUP_ID, pattern=r"/listar"))
    async def cmd_listar(event):
        logger.info("Comando /listar recebido.")
        keywords = await db.get_keywords()
        if not keywords:
            await event.reply("Nenhuma palavra-chave cadastrada.")
            return
        lista = "\n".join(f"• {kw}" for kw in sorted(keywords))
        await event.reply(f"*Palavras-chave monitoradas ({len(keywords)}):*\n\n{lista}")

    @client.on(events.NewMessage(chats=CONTROL_GROUP_ID, pattern=r"/adicionar (.+)"))
    async def cmd_adicionar(event):
        keyword = event.pattern_match.group(1).strip()
        logger.info("Comando /adicionar: '%s'", keyword)
        inserted = await db.add_keyword(keyword)
        if inserted:
            await event.reply(f"✅ Palavra-chave {keyword.lower()} adicionada.")
        else:
            await event.reply(f"⚠️ A palavra-chave {keyword.lower()} já está cadastrada.")

    @client.on(events.NewMessage(chats=CONTROL_GROUP_ID, pattern=r"/remover (.+)"))
    async def cmd_remover(event):
        keyword = event.pattern_match.group(1).strip()
        logger.info("Comando /remover: '%s'", keyword)
        deleted = await db.remove_keyword(keyword)
        if deleted:
            await event.reply(f"🗑️ Palavra-chave {keyword.lower()} removida.")
        else:
            await event.reply(f"❌ Palavra-chave {keyword.lower()} não encontrada.")

    @client.on(events.NewMessage(chats=CONTROL_GROUP_ID, pattern=r"/ajuda"))
    async def cmd_ajuda(event):
        logger.info("Comando /ajuda recebido.")
        await event.reply(
            "*Comandos disponíveis:*\n\n"
            "/listar — lista todas as palavras-chave monitoradas\n"
            "/adicionar <palavra> — adiciona uma palavra-chave\n"
            "/remover <palavra> — remove uma palavra-chave\n"
            "/ajuda — mostra esta mensagem"
        )