import asyncio
import logging
from backend.src.sockets.socket_base import SocketBase
from utils.pw3365_parser import parse_raw_data
from core.services.insert_service import insert_dict_to_timescaledb
from config.config_loader import load_settings

logger = logging.getLogger(__name__)

# 設定読み込み
settings = load_settings()
PW3365_HOST = settings["pw3365"]["host"]
PW3365_PORT = settings["pw3365"]["port"]
DEFAULT_PERIOD = settings["pw3365"].get("period", 60)

HEADER_ON = ":HEADER ON\r\n"
SET_COMMAND = ":MEASure:ITEM:POWer 15,207,247,31,15,15\r\n"
DEFAULT_READ_COMMAND = ":MEASure:POWer?\r\n"

class PW3365Service(SocketBase):
    """HIOKI PW3365 専用サービス"""

    def __init__(self, host: str, port: int):
        super().__init__(host, port)
        self._initialized = False

    # オーバーライド
    def send_command(self, command: str) -> str | None:
        if not self.sock:
            raise ConnectionError("ソケットが接続されていません")

        try:
            # 初回だけ初期化シーケンス
            if not self._initialized:
                self.sock.sendall(HEADER_ON.encode())
                self.sock.recv(4096)
                self.sock.sendall(SET_COMMAND.encode())
                self.sock.recv(4096)
                # 暫定で毎回初期化（検知ワードを入れ込むため）
                # self._initialized = True

            # 実際のコマンド送信
            self.sock.sendall(command.encode())

            # ALL RIGHT が返るまでループ（暫定）
            raw_data = ""
            while "ALL RIGHT" not in raw_data:
                chunk = self.sock.recv(4096).decode().strip()
                raw_data += chunk

            return raw_data.replace("ALL RIGHT", "").strip()
        except Exception as e:
            logger.error(f"PW3365通信エラー: {e}")
            return None


# ====== 周期収集タスク ======
collection_task: asyncio.Task | None = None
collection_period = DEFAULT_PERIOD
pw3365 = PW3365Service(PW3365_HOST, PW3365_PORT)

async def fetch_current_measurement():
    """単発取得（DBには保存しない）"""
    loop = asyncio.get_running_loop()

    def _worker():
        pw3365.connect()
        try:
            raw_data = pw3365.send_command(DEFAULT_READ_COMMAND)
            return parse_raw_data(raw_data) if raw_data else None
        finally:
            pw3365.disconnect()

    return await loop.run_in_executor(None, _worker)


async def start_collection(period: int | None = None):
    """周期収集を開始しDBに保存"""
    global collection_task, collection_period
    if period:
        collection_period = period

    # 多重起動防止
    if collection_task is None or collection_task.done():
        collection_task = asyncio.create_task(_collection_loop())
    else:
        logger.info("収集タスクはすでに起動中です")


async def stop_collection():
    """周期収集を停止"""
    global collection_task
    if collection_task and not collection_task.done():
        collection_task.cancel()
        collection_task = None


async def _collection_loop():
    """周期収集ループ"""
    try:
        while True:
            loop = asyncio.get_running_loop()

            def _worker():
                pw3365.connect()
                try:
                    raw_data = pw3365.send_command(DEFAULT_READ_COMMAND)
                    if raw_data:
                        return parse_raw_data(raw_data)
                finally:
                    pw3365.disconnect()
                return None

            data = await loop.run_in_executor(None, _worker)
            if data:
                await insert_dict_to_timescaledb(data)

            await asyncio.sleep(collection_period)
    except asyncio.CancelledError:
        pass
