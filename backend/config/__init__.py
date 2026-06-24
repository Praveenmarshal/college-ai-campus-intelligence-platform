"""config package — exports settings, database, chromadb, and logger helpers."""

from .settings import get_config, config_by_name
from .database import MongoManager, get_db
from .chromadb_config import ChromaManager, get_collection
from .logger import setup_logger

__all__ = [
    "get_config",
    "config_by_name",
    "MongoManager",
    "get_db",
    "ChromaManager",
    "get_collection",
    "setup_logger",
]
