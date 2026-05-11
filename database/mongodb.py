import logging
from datetime import datetime, timezone

import motor.motor_asyncio

from config import MONGO_URI

logger = logging.getLogger(__name__)

_client: motor.motor_asyncio.AsyncIOMotorClient = None
_collection: motor.motor_asyncio.AsyncIOMotorCollection = None


async def connect() -> None:
    global _client, _collection
    logger.info("Conectando ao MongoDB Atlas...")
    _client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    db = _client["telegram_keyword_bot"]
    _collection = db["keywords"]
    # ping força a conexão real — confirma que o Atlas está acessível
    await _client.admin.command("ping")
    await _collection.create_index("keyword", unique=True)
    logger.info("MongoDB Atlas conectado e índice garantido.")


async def get_keywords() -> list[str]:
    cursor = _collection.find({}, {"_id": 0, "keyword": 1})
    docs = await cursor.to_list(length=None)
    return [doc["keyword"] for doc in docs]


async def add_keyword(keyword: str) -> bool:
    """Adiciona uma nova palavra-chave com timestamps.
    
    - created_at: Quando foi adicionada
    - updated_at: Quando foi atualizada pela última vez
    """
    keyword = keyword.lower().strip()
    try:
        now = datetime.now(timezone.utc)
        await _collection.insert_one({
            "keyword": keyword,
            "created_at": now,
            "updated_at": now
        })
        logger.info("Keyword adicionada: '%s' em %s", keyword, now.strftime("%d/%m/%Y %H:%M:%S"))
        return True
    except Exception as e:
        logger.warning("Keyword '%s' já existe ou erro ao inserir: %s", keyword, e)
        return False


async def remove_keyword(keyword: str) -> bool:
    keyword = keyword.lower().strip()
    result = await _collection.delete_one({"keyword": keyword})
    if result.deleted_count > 0:
        logger.info("Keyword removida: '%s'", keyword)
        return True
    logger.warning("Keyword não encontrada para remoção: '%s'", keyword)
    return False


async def get_session() -> str | None:
    """Recupera a sessão salva no MongoDB."""
    try:
        doc = await _client["telegram_keyword_bot"]["session"].find_one({"_id": "session"})
        if doc:
            logger.debug("✓ Sessão recuperada do MongoDB")
            return doc["value"]
        logger.warning("⚠️  Nenhuma sessão encontrada no MongoDB")
        return None
    except Exception as e:
        logger.error("Erro ao recuperar sessão: %s", e)
        return None


async def save_session(session_string: str) -> None:
    """Salva/atualiza a sessão no MongoDB com timestamps.
    
    - created_at: Criado apenas na primeira vez (não é atualizado)
    - updated_at: Atualizado toda vez que a sessão é salva
    """
    try:
        now = datetime.now(timezone.utc)
        await _client["telegram_keyword_bot"]["session"].update_one(
            {"_id": "session"},
            {
                "$set": {
                    "value": session_string,
                    "updated_at": now,
                    "expires_at": None  # Sessão StringSession não expira por timestamp
                },
                "$setOnInsert": {
                    "created_at": now  # Só adiciona se for novo documento
                }
            },
            upsert=True
        )
        logger.info("✓ Sessão atualizada em: %s", now.strftime("%d/%m/%Y %H:%M:%S"))
    except Exception as e:
        logger.error("❌ Erro ao salvar sessão no MongoDB: %s", e)