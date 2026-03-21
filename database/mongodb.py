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
    keyword = keyword.lower().strip()
    try:
        await _collection.insert_one(
            {"keyword": keyword, "added_at": datetime.now(timezone.utc)}
        )
        logger.info("Keyword adicionada: '%s'", keyword)
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