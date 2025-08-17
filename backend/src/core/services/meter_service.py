# meter_service.py
# 計測器通信処理

async def get_latest_data():
    # 計測器の最新データを返すサンプル
    return {"voltage": 220, "current": 5}

async def start_collection():
    # 計測器データ収集開始
    return {"status": "started"}

async def stop_collection():
    # 計測器データ収集停止
    return {"status": "stopped"}


