import asyncio
import logging

from pyrogram import Client, idle

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
    await db.connect()  # lança exceção se o Atlas estiver inacessível

    app = Client(
        name="keyword_monitor",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STRING,
    )

    command_handler.register(app)
    message_handler.register(app)

    async with app:
        me = await app.get_me()
        logger.info("Autenticado como: %s (id=%s)", me.first_name, me.id)
        
        # Carrega todos os chats na sessão (grupos, canais, privados)
        await app.get_dialogs()
        logger.info("Dialogs carregados.")
        
        logger.info("Bot ativo. Aguardando mensagens...")
        try:
            await app.get_chat(CONTROL_GROUP_ID)
            await app.send_message(CONTROL_GROUP_ID, "🟢 Bot iniciado.")
        except Exception as e:
            logger.warning("Não foi possível enviar mensagem de startup: %s", e)
        await idle()

    logger.info("Bot encerrado.")


if __name__ == "__main__":
    asyncio.run(main())