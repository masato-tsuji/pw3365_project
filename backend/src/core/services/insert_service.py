# backend/src/core/services/insert_service.py
import asyncio
from datetime import datetime
from typing import Dict
from src.utils.get_mac_id import get_representative_mac
from src.core.db import get_db_pool

CATEGORY_KEYS = {
    "pw3365_voltage": ["u", "ufnd", "udeg", "upeak"],
    "pw3365_current": ["i", "ifnd", "ideg", "ipeak"],
    "pw3365_power": ["p", "pf", "s", "q", "dpf"],
    "pw3365_energy": ["wp", "wqlag", "wqlead", "ecost"],
    "pw3365_demand": ["wp_dem", "pdem", "qdem", "pf_dem", "pdemplus"],  # ← pdemplus 追加
    "pw3365_freq": ["freq"]
}

async def insert_dict_to_timescaledb(data_dict: Dict):
    normalized_data = {k.lower(): v for k, v in data_dict.items()}
    normalized_data["device_id"] = get_representative_mac() or "unknown"
    normalized_data["device_name"] = data_dict.get("device_name")

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        for table_name, prefixes in CATEGORY_KEYS.items():
            sub_dict = {
                k: v for k, v in normalized_data.items()
                if any(k.startswith(prefix) for prefix in prefixes) and k != "status"
            }

            if len(sub_dict) == 0:
                print(f"Skipped {table_name}: no relevant data.")
                continue

            sub_dict["date_time"] = normalized_data["date_time"]
            sub_dict["device_id"] = normalized_data["device_id"]
            sub_dict["device_name"] = normalized_data["device_name"]

            columns = ', '.join(sub_dict.keys())
            placeholders = ', '.join([f"${i+1}" for i in range(len(sub_dict))])
            values = list(sub_dict.values())
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders});"

            try:
                async with conn.transaction():
                    await conn.execute(query, *values)
                    # print(f"Inserted into {table_name}.")
            except Exception as e:
                print(f"Error inserting into {table_name}: {e}")