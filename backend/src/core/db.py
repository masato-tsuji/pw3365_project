# app/core/db.py
# asyncpg接続プール

import asyncio
import asyncpg
from app.config.config_loader import load_settings

_pool = None

async def init_db_pool():
    global _pool
    if _pool is None:
        settings = load_settings()
        _pool = await asyncpg.create_pool(
            host=settings["db"]["host"],
            port=settings["db"]["port"],
            user=settings["db"]["user"],
            password=settings["db"]["password"],
            database=settings["db"]["dbname"],
            min_size=1,
            max_size=10
        )
    return _pool

async def get_db_pool():
    global _pool
    if _pool is None:
        await init_db_pool()
    return _pool
