from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker,AsyncSession
from src.core.config import get_settings


settings = get_settings()


engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=settings.APP_DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,
)


AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


_AFTER_COMMIT_CALLBACKS_KEY = "after_commit_callbacks"
AfterCommitCallback = Callable[[], Awaitable[None]]


def add_after_commit_callback(
    session: AsyncSession,
    callback: AfterCommitCallback,
) -> None:
    """Register async work that must run only after a successful commit."""
    callbacks = session.info.setdefault(_AFTER_COMMIT_CALLBACKS_KEY, [])
    callbacks.append(callback)


async def run_after_commit_callbacks(session: AsyncSession) -> None:
    callbacks = session.info.pop(_AFTER_COMMIT_CALLBACKS_KEY, [])
    for callback in callbacks:
        await callback()


def clear_after_commit_callbacks(session: AsyncSession) -> None:
    session.info.pop(_AFTER_COMMIT_CALLBACKS_KEY, None)


async def get_db() -> AsyncSession: # type: ignore
    """
    FastAPI Depends 注入, 自动提交和异常回滚数据库
    """
    # 上下文管理器，自动关闭数据库会话

    async with AsyncSessionLocal() as session:
        try:
            yield session # type: ignore
            await session.commit()
        except Exception:
            clear_after_commit_callbacks(session)
            await session.rollback()
            raise

        await run_after_commit_callbacks(session)
