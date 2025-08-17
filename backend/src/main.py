# main.py
# FastAPI エントリーポイント

from backend.src.api import pw3365_api
from fastapi import FastAPI
from api import network
from core.db import init_db
from config.config_loader import load_settings
import uvicorn

app = FastAPI(title="Meter Monitoring API")

# 設定読み込み
settings = load_settings()

# DB初期化
init_db(settings["db"])

# ルーター登録
app.include_router(network.router, prefix="/network", tags=["network"])
app.include_router(pw3365_api.router, prefix="/meter", tags=["meter"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

