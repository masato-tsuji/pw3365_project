import asyncio
import logging
from src.sockets.socket_base import SocketBase
from src.utils.pw3365_parser import parse_raw_data
from src.core.services.insert_service import insert_dict_to_timescaledb
from src.config.config_loader import load_config

logger = logging.getLogger(__name__)

# 設定読み込み
settings = load_config()
PW3365_HOST = settings["pw3365"]["host"]
PW3365_PORT = settings["pw3365"]["port"]
DEFAULT_PERIOD = settings["pw3365"].get("period", 60)

HEADER_ON = ":HEADER ON\r\n"
SET_COMMAND = ":MEASure:ITEM:POWer 15,207,247,31,15,15\r\n"
DEFAULT_READ_COMMAND = ":MEASure:POWer?\r\n"

class PW3365Service(SocketBase):
    """HIOKI PW3365 専用サービス（完全非同期版）"""

    def __init__(self, host: str, port: int, period: int = DEFAULT_PERIOD):
        super().__init__(host, port)
        self._initialized = False
        self.collection_task: asyncio.Task | None = None
        self.collection_period = period

    async def connect(self):
        """PW3365との接続を確立"""
        await super().connect()

    async def disconnect(self):
        """PW3365との接続を切断"""
        await super().disconnect()

    def is_alive(self) -> bool:
        """接続状態を確認"""
        return self.sock is not None

    async def send_command(self, command: str) -> str | None:
        """コマンド送信と応答取得"""
        if not self.sock:
            raise ConnectionError("ソケットが接続されていません")

        try:
            if not self._initialized:
                await self.sock.sendall(HEADER_ON.encode())
                await self.sock.recv(4096)
                await self.sock.sendall(SET_COMMAND.encode())
                await self.sock.recv(4096)
                # self._initialized = True

            await self.sock.sendall(command.encode())

            raw_data = ""
            while "ALL RIGHT" not in raw_data:
                chunk = (await self.sock.recv(4096)).decode().strip()
                raw_data += chunk

            return raw_data.replace("ALL RIGHT", "").strip()
        except Exception as e:
            logger.error(f"PW3365通信エラー: {e}")
            return None

    async def fetch_current_measurement(self) -> dict | None:
        """単発取得（DBには保存しない）"""
        await self.connect()
        try:
            raw_data = await self.send_command(DEFAULT_READ_COMMAND)
            return parse_raw_data(raw_data) if raw_data else None
        finally:
            await self.disconnect()

    async def start_collection(self, period: int | None = None):
        """周期収集を開始しDBに保存"""
        if period:
            self.collection_period = period

        if self.collection_task is None or self.collection_task.done():
            self.collection_task = asyncio.create_task(self._collection_loop())
        else:
            logger.info("収集タスクはすでに起動中です")

    async def stop_collection(self):
        """周期収集を停止"""
        if self.collection_task and not self.collection_task.done():
            self.collection_task.cancel()
            self.collection_task = None

    async def _collection_loop(self):
        """周期収集ループ"""
        try:
            while True:
                await self.connect()
                try:
                    raw_data = await self.send_command(DEFAULT_READ_COMMAND)
                    if raw_data:
                        data = parse_raw_data(raw_data)
                        await insert_dict_to_timescaledb(data)
                finally:
                    await self.disconnect()

                await asyncio.sleep(self.collection_period)
        except asyncio.CancelledError:
            pass
