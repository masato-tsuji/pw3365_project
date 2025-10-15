from fastapi import APIRouter, HTTPException, Query
from src.core.services.pw3365_service import PW3365Service
from src.core.services.network_service import network_status
from src.sockets.lan_socket import LanSocket
from src.sockets.usb_socket import UsbSocket
from src.config.config_loader import load_config
from pydantic import BaseModel
from datetime import datetime


router = APIRouter(prefix="/pw3365", tags=["meter"])
settings = load_config()

# 通信方式ごとのインスタンスを保持
pw3365_instances = {}

def get_pw3365_instance(comm_type: str) -> PW3365Service:
    if comm_type not in pw3365_instances:
        if comm_type == "lan":
            socket = LanSocket(
                host=settings["pw3365"]["host"],
                port=settings["pw3365"]["port"]
            )
        elif comm_type == "usb":
            socket = UsbSocket(
                port=settings["pw3365"]["port"],
                baudrate=settings["pw3365"].get("baudrate", 115200)
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid communication type")
        pw3365_instances[comm_type] = PW3365Service(socket=socket)
    return pw3365_instances[comm_type]

class StartRequest(BaseModel):
    period: int | None = None
    device_name: str | None = None

def _check_network():
    if not network_status.get("ok", False):
        raise HTTPException(status_code=503, detail=f"Network unavailable: {network_status.get('message')}")

@router.get("/current")
async def get_current_measurement(type: str = Query(default="lan")):
    _check_network()
    pw3365 = get_pw3365_instance(type)
    data = await pw3365.fetch_current_measurement()
    return {"status": "ok", "data": data} if data else {"status": "error", "data": None}

# @router.post("/start")
# async def start_collection(req: StartRequest, type: str = Query(default="lan")):
#     _check_network()
#     pw3365 = get_pw3365_instance(type)
#     await pw3365.start_collection(req.period)
#     return {"status": "started", "period": pw3365.collection_period}


@router.post("/start")
async def start_collection(req: StartRequest, type: str = Query(default="lan")):
    _check_network()
    pw3365 = get_pw3365_instance(type)

    # device_name のデフォルト値を補完
    device_name = req.device_name or f"pw3365_{datetime.now().strftime('%Y%m%d')}"

    await pw3365.start_collection(req.period, device_name=device_name)

    return {
        "status": "started",
        "period": pw3365.collection_period,
        "device_name": device_name
    }


@router.post("/stop")
async def stop_collection(type: str = Query(default="lan")):
    _check_network()
    pw3365 = get_pw3365_instance(type)
    await pw3365.stop_collection()
    return {"status": "stopped"}


@router.get("/status")
async def stop_collection(type: str = Query(default="lan")):
    _check_network()
    pw3365 = get_pw3365_instance(type)
    return {"status": pw3365.get_status()}

