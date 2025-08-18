from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api import pw3365_api
from src.api import network_api
from src.core.services.network_service import monitor_network
from src.core.db import init_db_pool
from src.config.config_loader import load_config
import asyncio
import uvicorn

# 設定読み込み
settings = load_config()

# lifespan イベントハンドラ
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_pool()
    asyncio.create_task(monitor_network())
    yield
    # 必要なら shutdown 時の処理もここに書けます

# FastAPI アプリ定義
app = FastAPI(title="Meter Monitoring API", lifespan=lifespan)

# ルーター登録
app.include_router(network_api.router, prefix="/network", tags=["network"])
app.include_router(pw3365_api.router, prefix="/meter", tags=["meter"])

# ローカル実行用
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
