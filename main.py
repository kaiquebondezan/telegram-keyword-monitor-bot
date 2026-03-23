import asyncio
import logging

from telethon import TelegramClient, events
from telethon.sessions import StringSession

import database.mongodb as db
import handlers.command_handler as command_handler
import handlers.message_handler as message_handler
from config import API_HASH, API_ID, CONTROL_GROUP_ID, SESSION_STRING

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    await db.connect()

    client = TelegramClient(
        StringSession(SESSION_STRING),
        api_id=API_ID,
        api_hash=API_HASH,
    )

    await client.start()
    me = await client.get_me()
    logger.info("Autenticado como: %s (id=%s)", me.first_name, me.id)

    # Registra handlers
    command_handler.register(client)
    message_handler.register(client)

    logger.info("Bot ativo. Aguardando mensagens...")
    try:
        await client.send_message(CONTROL_GROUP_ID, "🟢 Bot iniciado.")
    except Exception as e:
        logger.warning("Não foi possível enviar mensagem de startup: %s", e)

    await client.run_until_disconnected()
    logger.info("Bot encerrado.")


if __name__ == "__main__":
    asyncio.run(main())