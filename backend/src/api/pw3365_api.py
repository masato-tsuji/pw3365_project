# backend/src/api/pw3365_api.py
from fastapi import APIRouter, HTTPException
from src.core.services.pw3365_service import pw3365
from src.core.services.network_service import network_status
from pydantic import BaseModel

router = APIRouter(prefix="/pw3365", tags=["PW3365"])

class StartRequest(BaseModel):
    period: int | None = None  # 秒単位、未指定の場合は設定値を使用

def _check_network():
    """ネットワーク状態を確認し、異常なら例外を投げる"""
    if not network_status.get("ok", False):
        raise HTTPException(status_code=503, detail=f"Network unavailable: {network_status.get('message')}")

@router.get("/current")
async def get_current_measurement():
    """
    単発取得（DBには保存せず表示更新用）
    """
    _check_network()
    data = await pw3365.fetch_current_measurement()
    if data:
        return {"status": "ok", "data": data}
    return {"status": "error", "data": None}

@router.post("/start")
async def start_collection(req: StartRequest):
    """
    周期収集開始（DBに保存）
    """
    _check_network()
    period = req.period if req.period is not None else pw3365.collection_period
    await pw3365.start_collection(period)
    return {"status": "started", "period": pw3365.collection_period}

@router.post("/stop")
async def stop_collection():
    """
    周期収集停止
    """
    _check_network()
    await pw3365.stop_collection()
    return {"status": "stopped"}
