# backend/src/core/services/network_service.py
import asyncio
import logging
from src.utils.netcheck import is_reachable_main_db

logger = logging.getLogger(__name__)

# 監視結果を保持する変数（APIから参照）
network_status = {"ok": True, "message": "初期状態"}

async def monitor_network(interval: int = 10):
    """
    ネットワーク監視ループ
    interval: 監視周期（秒）
    """
    global network_status
    while True:
        try:
            # 実際のネットワークチェック処理をここに実装
            # 例: pingやTCP接続チェックなど
            # 成功した場合

            res = is_reachable_main_db()

            if not res:
                raise Exception("メインDBへの接続に失敗しました。")     

            network_status["ok"] = True
            network_status["message"] = "ネットワーク正常"
        except Exception as e:
            network_status["ok"] = False
            network_status["message"] = str(e)
            logger.error(f"ネットワーク監視エラー: {e}")
        await asyncio.sleep(interval)
