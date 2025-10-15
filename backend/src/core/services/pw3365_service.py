import asyncio
import logging
from datetime import datetime, timedelta
from src.sockets.socket_base import SocketBase
from src.utils.pw3365_parser import parse_raw_data
from src.core.services.insert_service import insert_dict_to_timescaledb
from src.config.config_loader import load_config

logger = logging.getLogger(__name__)

# 定数定義
HEADER_ON = ":HEADER ON"
SET_COMMAND = ":MEASure:ITEM:POWer 15,207,247,31,15,15"
DEFAULT_READ_COMMAND = ":MEASure:POWer?"

settings = load_config()
DEFAULT_PERIOD = settings["pw3365"].get("period", 5)

# PW3365サービスクラス
class PW3365Service:
    """HIOKI PW3365 専用サービス（完全非同期版）"""

    def __init__(self, socket: SocketBase, period: int = DEFAULT_PERIOD):
        self.socket = socket
        self.collection_period = period
        self._initialized = False
        self.collection_task: asyncio.Task | None = None
        self._collecting = False
        self.device_name = None

    async def connect(self):
        await self.socket.connect()

    async def disconnect(self):
        await self.socket.disconnect()

    async def send_command(self, command: str) -> str | None:
        try:
            if not self._initialized:
                await self.socket.request(HEADER_ON)
                await self.socket.request(SET_COMMAND)
                self._initialized = True

            raw_data = await self.socket.request(command)

            if "ALL RIGHT" in raw_data:
                return raw_data.replace("ALL RIGHT", "").strip()
            return raw_data.strip()
        except Exception as e:
            logger.error(f"PW3365通信エラー: {e}")
            return None


    def _get_next_aligned_time(self, interval_minutes: int, now: datetime = None) -> datetime:
        if 60 % interval_minutes != 0:
            raise ValueError("Interval must be a divisor of 60")
        now = now or datetime.now()
        base_hour = now.replace(minute=0, second=0, microsecond=0)
        alignment_points = [base_hour + timedelta(minutes=i) for i in range(0, 60, interval_minutes)]
        for point in alignment_points:
            if point > now:
                return point
        return base_hour + timedelta(hours=1)

    # コレクション状態取得
    def get_status(self) -> str:
        return "started" if self._collecting else "stopped"

    # 単発取得（DBには保存せず表示更新用）
    async def fetch_current_measurement(self) -> dict | None:
        await self.connect()
        try:
            raw_data = await self.send_command(DEFAULT_READ_COMMAND)
            return parse_raw_data(raw_data) if raw_data else None
        finally:
            await self.disconnect()

    # コレクション開始
    async def start_collection(self, period: int | None = None, device_name: str | None = None):
        if period:
            self.collection_period = period

        self.device_name = device_name

        if not self._collecting:
            self._collecting = True
            # 次の周期開始まで待機
            next_start = self._get_next_aligned_time(self.collection_period)    
            wait_seconds = (next_start - datetime.now()).total_seconds()
            print(f"Waiting {wait_seconds:.1f} seconds until next aligned start at {next_start}")
            await asyncio.sleep(wait_seconds)
            # 収集開始
            self.collection_task = asyncio.create_task(self._collection_loop())
            print("Collection task started.")
        else:
            print("Collection task already running.")

    # コレクション停止
    async def stop_collection(self):
        if self._collecting:
            self._collecting = False
            print("Stop requested.")
        else:
            print("No active collection task.")

    # コレクションループ
    async def _collection_loop(self):
        try:
            while True:
                if not self._collecting:
                    print("Collection flag is False. Exiting loop.")
                    break

                # print("Collection flag is True. Continuing loop.")
                await self.connect()
                try:
                    raw_data = await self.send_command(DEFAULT_READ_COMMAND)
                    # print(f"Raw data: {raw_data}")
                    if raw_data:
                        data = parse_raw_data(raw_data)
                        data["device_name"] = self.device_name
                        # print(f"Parsed data: {data}")
                        await insert_dict_to_timescaledb(data)
                except Exception as e:
                    print(f"Error in collection loop: {e}")
                finally:
                    await self.disconnect()

                await asyncio.sleep(self.collection_period * 60)    # 次の周期まで待機（分）
            print("Collection loop exited.")
        except Exception as e:
            print(f"Unexpected error in collection loop: {e}")

