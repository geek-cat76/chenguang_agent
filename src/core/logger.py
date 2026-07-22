import sys
from pathlib import Path
from loguru import logger
from src.core.config import get_settings


def setup_logger() -> None:
    settings = get_settings()
    logger.remove()

    # 控制台
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # 文件
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.add(
        str(log_dir / "{time:YYYY-MM-DD}.log"),
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        # 每天 新开一个日志文件
        rotation="00:00",
        # 保留30天的日志文件
        retention="30 days",
        # 压缩日志文件的格式
        compression="gz",
        # 日志文件的编码格式
        encoding="utf-8",
    )