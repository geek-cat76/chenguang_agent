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


async def get_db() -> AsyncSession: # type: ignore
    """
    FastAPI Depends 注入, 自动提交和异常回滚数据库
    """
    # 上下文管理器，自动关闭数据库会话

    async with AsyncSessionLocal() as session:
        try:
            yield session # type: ignore
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
