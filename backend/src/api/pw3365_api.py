from fastapi import APIRouter, HTTPException, Query
from src.core.services.pw3365_service import PW3365Service
from src.core.services.network_service import network_status
from src.sockets.lan_socket import LanSocket
from src.sockets.usb_socket import UsbSocket
from src.config.config_loader import load_config
from pydantic import BaseModel

router = APIRouter(prefix="/meter", tags=["meter"])
settings = load_config()

class StartRequest(BaseModel):
    period: int | None = None  # 秒単位、未指定の場合は設定値を使用

def _check_network():
    if not network_status.get("ok", False):
        raise HTTPException(status_code=503, detail=f"Network unavailable: {network_status.get('message')}")

def get_socket(comm_type: str):
    if comm_type == "usb":
        return UsbSocket(
            port=settings["pw3365"]["port"],
            baudrate=settings["pw3365"].get("baudrate", 115200)
        )
    elif comm_type == "lan":
        return LanSocket(
            host=settings["pw3365"]["host"],
            port=settings["pw3365"]["port"]
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid communication type")

@router.get("/current")
async def get_current_measurement(type: str = Query(default="lan", description="通信方式: lan または usb")):
    """
    単発取得（DBには保存せず表示更新用）
    通信方式はクエリパラメータで指定（例: ?type=usb）。未指定時はLAN。
    """
    _check_network()
    socket = get_socket(type)
    pw3365 = PW3365Service(socket=socket)
    data = await pw3365.fetch_current_measurement()
    return {"status": "ok", "data": data} if data else {"status": "error", "data": None}

@router.post("/start")
async def start_collection(req: StartRequest, type: str = Query(default="lan", description="通信方式: lan または usb")):
    """
    周期収集開始（DBに保存）
    """
    _check_network()
    socket = get_socket(type)
    pw3365 = PW3365Service(socket=socket)
    period = req.period if req.period is not None else pw3365.collection_period
    await pw3365.start_collection(period)
    return {"status": "started", "period": pw3365.collection_period}

@router.post("/stop")
async def stop_collection(type: str = Query(default="lan", description="通信方式: lan または usb")):
    """
    周期収集停止
    """
    _check_network()
    socket = get_socket(type)
    pw3365 = PW3365Service(socket=socket)
    await pw3365.stop_collection()
    return {"status": "stopped"}

