# src/core/db.py
# asyncpg接続プール

import asyncio
import asyncpg
from src.config.config_loader import load_config

_pool = None

async def init_db_pool():
    global _pool
    if _pool is None:
        db_conf = load_config()["db"]['edge']
        _pool = await asyncpg.create_pool(
            host=db_conf["host"],
            port=db_conf["port"],
            user=db_conf["user"],
            password=db_conf["password"],
            database=db_conf["dbname"],
            min_size=1,
            max_size=10
        )
    return _pool

async def get_db_pool():
    global _pool
    if _pool is None:
        await init_db_pool()
    return _pool

