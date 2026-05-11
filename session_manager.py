"""
Gerenciador de sessão Telethon com reconexão automática e refresh.
Resolve problemas de expiração de sessão com monitoramento contínuo.
"""

import asyncio
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession

import database.mongodb as db

logger = logging.getLogger(__name__)

MAX_RECONNECT_ATTEMPTS = 10
RECONNECT_DELAY = 5  # segundos
SESSION_REFRESH_INTERVAL = 3600  # 1 hora


class SessionManager:
    """Gerencia a sessão Telegram com reconexão automática."""
    
    def __init__(self, api_id: int, api_hash: str):
        self.api_id = api_id
        self.api_hash = api_hash
        self.client: TelegramClient | None = None
        self.reconnect_attempts = 0
        self.is_connected = False
        self.last_session_update = None
        
    async def connect(self) -> TelegramClient:
        """Conecta ao Telegram usando sessão armazenada."""
        logger.info("Iniciando gerenciador de sessão...")
        
        session_str = await db.get_session()
        if not session_str:
            raise RuntimeError(
                "❌ Nenhuma sessão encontrada no MongoDB.\n"
                "Execute setup_session.py primeiro para autenticar."
            )
        
        self.client = TelegramClient(
            StringSession(session_str),
            api_id=self.api_id,
            api_hash=self.api_hash,
            auto_reconnect=True,  # Reconexão automática
            connection_retries=5,
            retry_delay=3,
        )
        
        await self.client.connect()
        
        # Valida se a sessão ainda é válida
        if not await self.client.is_user_authorized():
            logger.error("❌ Sessão expirada ou inválida!")
            raise RuntimeError(
                "Sessão expirada. Execute setup_session.py novamente."
            )
        
        me = await self.client.get_me()
        logger.info("✅ Autenticado como: %s (id=%s)", me.first_name, me.id)
        self.is_connected = True
        self.reconnect_attempts = 0
        
        # Salva a sessão (pode ter sido atualizada)
        await self._save_session()
        
        return self.client
    
    async def _save_session(self) -> None:
        """Salva a sessão atual no MongoDB."""
        if self.client:
            session_str = StringSession.save(self.client.session)
            await db.save_session(session_str)
            self.last_session_update = asyncio.get_event_loop().time()
            logger.debug("✓ Sessão salva no MongoDB")
    
    async def maintain_connection(self) -> None:
        """Monitora a conexão e reconecta se necessário."""
        if not self.client:
            return
        
        while True:
            try:
                # Verifica a cada 30 segundos se está conectado
                await asyncio.sleep(30)
                
                if self.client.is_connected():
                    self.is_connected = True
                    self.reconnect_attempts = 0
                    
                    # Atualiza sessão a cada 1 hora
                    current_time = asyncio.get_event_loop().time()
                    if (self.last_session_update is None or 
                        current_time - self.last_session_update > SESSION_REFRESH_INTERVAL):
                        await self._save_session()
                else:
                    logger.warning("⚠️  Conexão perdida! Tentando reconectar...")
                    await self._handle_reconnect()
                    
            except Exception as e:
                logger.error("Erro ao monitorar conexão: %s", e)
                await asyncio.sleep(5)
    
    async def _handle_reconnect(self) -> None:
        """Tenta reconectar com backoff exponencial."""
        self.is_connected = False
        
        while self.reconnect_attempts < MAX_RECONNECT_ATTEMPTS:
            try:
                self.reconnect_attempts += 1
                delay = RECONNECT_DELAY * (2 ** (self.reconnect_attempts - 1))
                
                logger.info(
                    "🔄 Tentativa de reconexão %d/%d em %d segundos...",
                    self.reconnect_attempts,
                    MAX_RECONNECT_ATTEMPTS,
                    delay
                )
                
                await asyncio.sleep(delay)
                
                if self.client:
                    await self.client.connect()
                    
                    if await self.client.is_user_authorized():
                        logger.info("✅ Reconectado com sucesso!")
                        self.is_connected = True
                        self.reconnect_attempts = 0
                        await self._save_session()
                        return
                    else:
                        logger.warning("⚠️  Sessão inválida após reconexão")
                        raise RuntimeError("Sessão expirada")
                        
            except Exception as e:
                logger.warning(
                    "Reconexão falhou (tentativa %d): %s",
                    self.reconnect_attempts, e
                )
        
        logger.critical(
            "❌ Falha em reconectar após %d tentativas. Encerrando.",
            MAX_RECONNECT_ATTEMPTS
        )
        raise RuntimeError("Falha persistente em reconectar ao Telegram")
    
    async def disconnect(self) -> None:
        """Desconecta graciosamente."""
        if self.client:
            try:
                await self._save_session()  # Salva antes de desconectar
                await self.client.disconnect()
                logger.info("Bot desconectado graciosamente.")
            except Exception as e:
                logger.error("Erro ao desconectar: %s", e)
