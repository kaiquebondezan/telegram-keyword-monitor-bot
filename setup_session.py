import asyncio
from datetime import datetime, timezone
from telethon import TelegramClient
from telethon.sessions import StringSession
from config import API_ID, API_HASH, MONGO_URI
import motor.motor_asyncio

async def main():
    print("\n" + "="*60)
    print("🔐 Setup de Sessão Telegram")
    print("="*60)
    print("\nSiga as instruções para autenticar com sua conta Telegram...\n")
    
    # Autentica interativamente
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        session_str = client.session.save()
    
    # Salva direto no MongoDB com timestamps
    db_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    now = datetime.now(timezone.utc)
    
    result = await db_client["telegram_keyword_bot"]["session"].update_one(
        {"_id": "session"},
        {
            "$set": {
                "value": session_str,
                "updated_at": now,
                "expires_at": None
            },
            "$setOnInsert": {
                "created_at": now  # Só adiciona se for novo documento
            }
        },
        upsert=True
    )
    
    db_client.close()
    
    print("\n" + "="*60)
    print("✅ Sessão salva no MongoDB com sucesso!")
    print("="*60)
    print(f"\nDetalhes:")
    print(f"  - Criado em: {now.strftime('%d/%m/%Y %H:%M:%S')} (BRT-3)")
    print(f"  - Atualizado em: {now.strftime('%d/%m/%Y %H:%M:%S')} (BRT-3)")
    print(f"  - Documento inserido: {result.upserted_id is not None}")
    print(f"\n💡 Agora você pode rodar: python main.py\n")

if __name__ == "__main__":
    asyncio.run(main())