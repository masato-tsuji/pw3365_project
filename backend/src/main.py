# main.py
from backend.src.api import pw3365_api
from fastapi import FastAPI
from backend.src.api import network_api  # APIで状態取得する場合
from backend.src.core.services.network_service import monitor_network
from backend.src.core.db import init_db
from backend.src.config.config_loader import load_settings
import asyncio
import uvicorn

app = FastAPI(title="Meter Monitoring API")

# 設定読み込み
settings = load_settings()

# DB初期化
init_db(settings["db"])

# ルーター登録
app.include_router(network_api.router, prefix="/network", tags=["network"])
app.include_router(pw3365_api.router, prefix="/meter", tags=["meter"])

# バックグラウンドでネットワーク監視を起動
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitor_network())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
