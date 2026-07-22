from fastapi import FastAPI
import asyncio
from src.middlewares.logging import LoggingMiddleware
from src.core.exceptions import register_exception_handlers
from src.core.logger import setup_logger
from src.core.config import get_settings
from loguru import logger
from src.infra.database import engine
from contextlib import asynccontextmanager

from src.modules.user.api import router as api_router
from src.modules.captcha.api import router as captcha_router
from src.modules.auth.api import router as auth_router



@asynccontextmanager
async def lifespan(app: FastAPI):

    # 初始化日志
    setup_logger()
    settings = get_settings()
    logger.info(f"{settings.APP_NAME} starting | env={settings.APP_ENV}")
    
    yield

    await engine.dispose()
    logger.info(f"{settings.APP_NAME} stopping | env={settings.APP_ENV}")


def create_app() -> FastAPI:
    """
    创建 FastAPI 应用
    1. 基础配置
    2. 中间件配置
    3. 异常处理配置
    4. 路由配置
    5. 生命周期感知配置
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )
    # 中间件配置
    app.add_middleware(LoggingMiddleware)

    # 异常处理配置
    register_exception_handlers(app,)

    # 路由配置
    app.include_router(api_router,prefix="/api/v1")
    app.include_router(captcha_router,prefix="/api/v1")
    app.include_router(auth_router,prefix="/api/v1")

    return app

app = create_app()

# 健康检查路由
@app.get("/health",tags=["系统API"],summary="健康检查") # type: ignore
async def root():
    return {"status": "ok"}
