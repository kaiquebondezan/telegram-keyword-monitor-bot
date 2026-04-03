import asyncio
import logging

from telethon import TelegramClient
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

SAVE_SESSION_INTERVAL = 3600  # salva a sessão a cada 1 hora


async def session_saver(client: TelegramClient) -> None:
    while True:
        await asyncio.sleep(SAVE_SESSION_INTERVAL)
        session_str = client.session.save()
        await db.save_session(session_str)
        logger.info("Sessão salva no MongoDB.")


async def main() -> None:
    await db.connect()

    # Carrega sessão do MongoDB se existir, senão usa a do env
    stored_session = await db.get_session()
    session_string = stored_session or SESSION_STRING
    if stored_session:
        logger.info("Sessão carregada do MongoDB.")
    else:
        logger.info("Usando SESSION_STRING do ambiente.")

    client = TelegramClient(
        StringSession(session_string),
        api_id=API_ID,
        api_hash=API_HASH,
    )

    await client.connect()
    if not await client.is_user_authorized():
        logger.error("SESSION_STRING inválida ou expirada. Gere uma nova sessão.")
        raise RuntimeError("SESSION_STRING inválida ou expirada.")

    me = await client.get_me()
    logger.info("Autenticado como: %s (id=%s)", me.first_name, me.id)

    # Salva a sessão atual imediatamente após conectar
    await db.save_session(client.session.save())
    logger.info("Sessão inicial salva no MongoDB.")

    command_handler.register(client)
    message_handler.register(client)

    logger.info("Bot ativo. Aguardando mensagens...")
    try:
        await client.send_message(CONTROL_GROUP_ID, "🟢 Bot iniciado.")
    except Exception as e:
        logger.warning("Não foi possível enviar mensagem de startup: %s", e)

    # Salva sessão periodicamente em background
    asyncio.create_task(session_saver(client))

    await client.run_until_disconnected()
    logger.info("Bot encerrado.")


if __name__ == "__main__":
    asyncio.run(main())