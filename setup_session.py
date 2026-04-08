import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from config import API_ID, API_HASH, MONGO_URI
import motor.motor_asyncio

async def main():
    # Autentica interativamente
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        session_str = client.session.save()
    
    # Salva direto no MongoDB
    db_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    await db_client["telegram_keyword_bot"]["session"].update_one(
        {"_id": "session"},
        {"$set": {"value": session_str}},
        upsert=True
    )
    db_client.close()
    print("Sessão salva no MongoDB com sucesso!")

if __name__ == "__main__":
    asyncio.run(main())