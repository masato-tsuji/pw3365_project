import asyncio
from backend.src.config.config_loader import config
from backend.src.utils.pw3365_parser import parse_raw_data
from backend.src.core.services.insert_service import insert_dict_to_timescaledb
import socket

class PW3365Service:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.collection_task: asyncio.Task | None = None
        self.collection_period: int = config["pw3365"]["period"]

    async def send_command(self, command: str) -> str | None:
        """PW3365にコマンド送信して応答を返す"""
        loop = asyncio.get_running_loop()

        def _blocking_socket():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
                s.sendall(b":HEADER ON\r\n")
                s.recv(4096)
                s.sendall(b":MEASure:ITEM:POWer 15,207,247,31,15,15\r\n")
                s.recv(4096)
                s.sendall(command.encode())
                raw_data = ""
                while "ALL RIGHT" not in raw_data:
                    raw_data += s.recv(4096).decode().strip()
                return raw_data.replace("ALL RIGHT", "")

        try:
            return await loop.run_in_executor(None, _blocking_socket)
        except Exception as e:
            print(f"PW3365通信エラー: {e}")
            return None

    async def fetch_current_measurement(self):
        """単発取得（DBには保存しない）"""
        raw_data = await self.send_command(":MEASure:POWer?")
        if raw_data:
            return parse_raw_data(raw_data)
        return None

    async def start_collection(self, period: int | None = None):
        """周期収集を開始しDBに保存"""
        if period:
            self.collection_period = period
        if self.collection_task is None or self.collection_task.done():
            self.collection_task = asyncio.create_task(self._collection_loop())

    async def stop_collection(self):
        """周期収集を停止"""
        if self.collection_task and not self.collection_task.done():
            self.collection_task.cancel()
            self.collection_task = None

    async def _collection_loop(self):
        """周期収集の内部ループ"""
        try:
            while True:
                raw_data = await self.send_command(":MEASure:POWer?")
                if raw_data:
                    data_dict = parse_raw_data(raw_data)
                    await insert_dict_to_timescaledb(data_dict)
                await asyncio.sleep(self.collection_period)
        except asyncio.CancelledError:
            pass

# 設定からインスタンス生成
pw3365 = PW3365Service(
    host=config["pw3365"]["host"],
    port=config["pw3365"]["port"]
)
