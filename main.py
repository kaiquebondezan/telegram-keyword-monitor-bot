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
    await db.connect()

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
        count = 0
        async for _ in app.get_dialogs(limit=0):
            count += 1
        logger.info("Dialogs carregados: %d chats.", count)
        
        # NOVO: Force updates desses chats específicos (SOLUÇÃO 1)
        logger.info("Forçando atualizações dos chats...")
        try:
            async for dialog in app.get_dialogs():
                if dialog.chat.id != CONTROL_GROUP_ID:
                    try:
                        await app.get_chat_history(dialog.chat.id, limit=1)
                    except:
                        pass
        except Exception as e:
            logger.warning("Erro ao forçar updates: %s", e)
        
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