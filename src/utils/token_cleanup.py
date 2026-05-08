import asyncio

from src.conf.config import settings
from src.db.session import sessionmanager
from src.repositories.token_repository import TokenRepository


async def cleanup_expired_tokens_once() -> int:
    async with sessionmanager.session() as db_session:
        token_repository = TokenRepository(db_session)
        return await token_repository.cleanup_expired_tokens()


async def token_cleanup_loop() -> None:
    while True:
        await cleanup_expired_tokens_once()
        await asyncio.sleep(settings.TOKEN_CLEANUP_INTERVAL_SECONDS)
