import psutil

def is_physical_interface(iface):
    # ループバックや仮想インターフェースを除外
    if iface == 'lo' or iface.startswith('Loopback'):
        return False

    virtual_keywords = ['virtual', 'vmware', 'vbox', 'docker', 'br-', 'tun', 'tap', 'wg', 'zt']
    iface_lower = iface.lower()
    if any(keyword in iface_lower for keyword in virtual_keywords):
        return False

    return True

def get_representative_mac():
    for iface, addrs in psutil.net_if_addrs().items():
        if not is_physical_interface(iface):
            continue
        for addr in addrs:
            if addr.family == psutil.AF_LINK:
                mac = addr.address
                safe_mac = mac.replace(":", "_").lower()
                if mac and mac != '00:00:00:00:00:00':
                    return safe_mac
    return None

# 実行例
# mac_address = get_representative_mac()
# print(f"Representative MAC address for DB key: {mac_address}")
