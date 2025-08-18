# src/core/services/insert_service.py
import asyncio
from typing import Dict
from src.core.db import get_db_pool
from src.utils.pw3365_parser import parse_raw_data

CATEGORY_KEYS = {
    "pw3365_voltage": ["U", "Ufnd", "Udeg"],
    "pw3365_current": ["I", "Ifnd", "Ideg", "Ipeak"],
    "pw3365_power": ["P", "PF", "S", "Q", "DPF"],
    "pw3365_energy": ["WP", "WQLAG", "WQLEAD", "Ecost"],
    "pw3365_demand": ["WP_dem", "Pdem", "Qdem", "PF_dem"],
    "pw3365_freq": ["Freq"]
}
COMMON_KEYS = ["device_id", "timestamp"]

async def insert_dict_to_timescaledb(data_dict: Dict):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            for table_name, prefixes in CATEGORY_KEYS.items():
                sub_dict = {k: v for k, v in data_dict.items() if any(k.startswith(p) for p in prefixes)}
                for ck in COMMON_KEYS:
                    if ck in data_dict:
                        sub_dict[ck] = data_dict[ck]
                if len(sub_dict) > len(COMMON_KEYS):
                    columns = ', '.join(sub_dict.keys())
                    placeholders = ', '.join([f"${i+1}" for i in range(len(sub_dict))])
                    values = list(sub_dict.values())
                    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders});"
                    try:
                        await conn.execute(query, *values)
                        print(f"Inserted into {table_name}.")
                    except Exception as e:
                        print(f"Error inserting into {table_name}: {e}")
