import contextlib

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from src.conf.config import settings

class DatabaseSessionManager:
    """Factory and context manager for asynchronous DB sessions."""
    def __init__(self, url: str):
        """Create engine and sessionmaker for provided database URL."""
        self._engine: AsyncEngine | None = create_async_engine(url)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self._engine
        )

    @contextlib.asynccontextmanager
    async def session(self):
        """Yield transactional session with rollback on DB errors."""
        if self._session_maker is None:
            raise Exception("Database session is not initialized")
        session = self._session_maker()
        try:
            yield session
        except SQLAlchemyError:
            await session.rollback()
            raise
        finally:
            await session.close()

sessionmanager = DatabaseSessionManager(settings.DATABASE_URL)

async def get_db():
    """FastAPI dependency that yields active database session."""
    async with sessionmanager.session() as session:
        yield session
