# Placeholder for test_db.py
import pytest
from src.core.db import get_db_pool

@pytest.mark.asyncio
async def test_get_db_pool():
    pool = await get_db_pool()
    assert pool is not None
