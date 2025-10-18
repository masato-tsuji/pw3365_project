# ネットワークの接続を確認するユーティリティモジュール
# 疎通があれば通信元と通信先のアドレスを返す
# 疎通がなければNoneを返す

import socket
from src.config.config_loader import load_config

def is_reachable_main_db():
    try:
        db_conf = load_config()["db"]["main"]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((db_conf['host'], db_conf.get('port', 5432)))
        src_ip = s.getsockname()[0]
        s.close()
        return {'src': src_ip, 'dst': db_conf['host']}
    except Exception:
        return None

if __name__ == "__main__":
    res = is_reachable_main_db()
    if res:
        print(f"Main DB is reachable from {res['src']} to {res['dst']}")
    else:
        print("Main DB is not reachable")
