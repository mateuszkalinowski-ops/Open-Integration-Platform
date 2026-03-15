from config import settings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,
)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:  # type: ignore[misc]
    async with async_session_factory() as session:
        yield session


async def set_rls_bypass(session: AsyncSession) -> None:
    """Enable admin bypass for RLS policies on the current transaction.

    Use this for cross-tenant operations: background jobs, verification
    agent, Kafka consumer, startup provisioning, etc.
    """
    await session.execute(text("SELECT set_config('app.rls_bypass', 'on', true)"))
