# backend/src/api/network_api.py
from fastapi import APIRouter
from src.core.services.network_service import network_status

router = APIRouter()

@router.get("/status")
async def get_network_status():
    """
    ネットワーク監視状態を取得
    """
    return network_status
