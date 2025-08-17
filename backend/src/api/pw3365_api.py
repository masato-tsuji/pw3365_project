from fastapi import APIRouter
from pydantic import BaseModel
from core.services.pw3365_service import (
    start_collection,
    stop_collection,
    fetch_current_measurement
)

router = APIRouter(prefix="/pw3365", tags=["PW3365"])

class StartRequest(BaseModel):
    period: int  # 秒単位

@router.post("/start")
async def start_meter(req: StartRequest):
    await start_collection(req.period)
    return {"status": "started", "period": req.period}

@router.post("/stop")
async def stop_meter():
    await stop_collection()
    return {"status": "stopped"}

@router.get("/current")
async def get_current_measurement():
    """
    Reactから単発取得。
    DBには保存せず表示更新用。
    """
    data = await fetch_current_measurement()
    if data:
        return {"status": "ok", "data": data}
    return {"status": "error", "data": None}
