from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import network

app = FastAPI()

# CORS設定（React開発用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# ルーター登録
app.include_router(network.router, prefix="/api")
