import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from config import API_ID, API_HASH

async def main():
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        print("\nNova SESSION_STRING para Telethon:")
        print(client.session.save())

if __name__ == "__main__":
    asyncio.run(main())