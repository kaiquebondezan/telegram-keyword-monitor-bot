import asyncio
import logging
import signal

import database.mongodb as db
import handlers.command_handler as command_handler
import handlers.message_handler as message_handler
from config import API_HASH, API_ID, CONTROL_GROUP_ID
from session_manager import SessionManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Flag de shutdown graciosa
shutdown_event = asyncio.Event()


async def main() -> None:
    """Inicia o bot com reconexão automática e monitoramento de sessão."""
    await db.connect()
    logger.info("=" * 60)
    logger.info("🤖 Telegram Keyword Monitor Bot - Versão com Auto-Reconexão")
    logger.info("=" * 60)

    # Inicializa gerenciador de sessão com reconexão automática
    session_mgr = SessionManager(api_id=API_ID, api_hash=API_HASH)
    
    try:
        # Conecta ao Telegram
        client = await session_mgr.connect()
        
        # Registra handlers
        command_handler.register(client)
        message_handler.register(client)

        # Inicia tarefas assíncronas
        run_task = asyncio.create_task(client.run_until_disconnected())
        monitor_task = asyncio.create_task(session_mgr.maintain_connection())
        shutdown_task = asyncio.create_task(shutdown_event.wait())

        # Mensagem de inicialização
        try:
            await client.send_message(CONTROL_GROUP_ID, "🟢 Bot iniciado e aguardando mensagens.")
        except Exception as e:
            logger.warning("⚠️  Não foi possível enviar mensagem de startup: %s", e)

        logger.info("✅ Bot ativo. Monitorando palavras-chave...")

        # Aguarda qualquer um dos eventos (desconexão, shutdown, etc)
        done, pending = await asyncio.wait(
            [run_task, monitor_task, shutdown_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        # Cancela as tarefas pendentes
        for task in pending:
            task.cancel()

        logger.info("🛑 Encerrando bot...")

    except RuntimeError as e:
        logger.error("❌ Erro de autenticação: %s", e)
        raise
    except Exception as e:
        logger.error("❌ Erro fatal: %s", e)
        raise
    finally:
        await session_mgr.disconnect()
        logger.info("✓ Bot encerrado.")


def signal_handler(sig, frame):
    """Manipula sinais para shutdown graciosa."""
    logger.info("📊 Sinal recebido, encerrando graciosamente...")
    shutdown_event.set()


if __name__ == "__main__":
    # Registra handlers para SIGINT e SIGTERM
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot interrompido pelo usuário.")
    except Exception as e:
        logger.error("Erro fatal não tratado: %s", e)
        raise


if __name__ == "__main__":
    asyncio.run(main())