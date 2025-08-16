import psutil
import socket
import subprocess
from fastapi import APIRouter

router = APIRouter()

def get_interface_status():
    interfaces = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()
    data = []

    for iface, stats in interfaces.items():
        if iface.startswith("lo"):  # ループバック除外
            continue

        ip_address = None
        for addr in addrs.get(iface, []):
            if addr.family == socket.AF_INET:
                ip_address = addr.address

        iface_info = {
            "interface": iface,
            "is_up": stats.isup,
            "speed": stats.speed,  # Mbps
            "mtu": stats.mtu,
            "ip_address": ip_addressjljhguilkjbikj
        }

        # Wi-FiインターフェースならSSIDと信号強度を追加
        if iface.startswith("wl"):
            wifi_info = get_wifi_info(iface)
            iface_info.update(wifi_info)

        data.append(iface_info)
    return data


def get_wifi_info(interface):
    """
    iwコマンドでSSIDと信号強度(dBm)を取得
    """
    try:
        result = subprocess.run(
            ["iw", "dev", interface, "link"],
            capture_output=True,
            text=True,
            check=True
        )
        ssid = None
        signal = None

        for line in result.stdout.splitlines():
            if "SSID" in line:
                ssid = line.split("SSID")[-1].strip()
            elif "signal" in line:
                signal = line.split("signal")[-1].strip()

        return {
            "ssid": ssid,
            "signal_strength": signal
        }
    except subprocess.CalledProcessError:
        return {
            "ssid": None,
            "signal_strength": None
        }


@router.get("/network/status")
async def network_status():
    """
    ネットワークインターフェース状態 + Wi-Fi詳細
    """
    return {
        "interfaces": get_interface_status()
    }
