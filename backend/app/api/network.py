import psutil
import socket
from fastapi import APIRouter

router = APIRouter()

def get_interface_status():
    interfaces = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()
    data = []

    for iface, stats in interfaces.items():
        if iface.startswith("lo"):  # ループバックは除外
            continue

        ip_address = None
        for addr in addrs.get(iface, []):
            if addr.family == socket.AF_INET:
                ip_address = addr.address

        data.append({
            "interface": iface,
            "is_up": stats.isup,
            "speed": stats.speed,   # Mbps
            "mtu": stats.mtu,
            "ip_address": ip_address
        })
    return data

@router.get("/network/status")
async def network_status():
    """
    ネットワークインターフェースの状態を取得
    """
    return {
        "interfaces": get_interface_status()
    }
