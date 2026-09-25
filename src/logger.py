from pathlib import Path
import sys

from loguru import logger

# Create logs directory

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"

LOG_DIR.mkdir(exist_ok=True)

# Remove Loguru's default logger

logger.remove() 

# Log messages to terminal

logger.add(
    sys.stdout,
    level="INFO",
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:"
        "<cyan>{function}</cyan>:"
        "<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    ),
)
#2026-08-25 13:05:32 | INFO  | src.usecase_1.retriever:retrieve:42 | Starting paper retrieval

# Log messages to file

logger.add(
    LOG_DIR / "app.log",
    level="DEBUG",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    encoding="utf-8",
    format=(
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    ),
)