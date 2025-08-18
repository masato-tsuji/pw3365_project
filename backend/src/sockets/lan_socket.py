# backend/src/sockets/lan_socket.py
import asyncio
import logging
import platform

from src.sockets.socket_base import SocketBase, SocketError

logger = logging.getLogger(__name__)


class LanSocket(SocketBase):
    """
    LAN (TCP/IP) 通信実装クラス。
    - connect/disconnect で TCP セッションを管理
    - send_command でコマンド送受信
    - is_alive は ping による疎通確認を実装
    """

    def __init__(self, host: str, port: int, timeout: float = 5.0) -> None:
        super().__init__(name=f"LAN({host}:{port})", timeout=timeout)
        self._host = host
        self._port = port
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def connect(self) -> None:
        try:
            self._reader, self._writer = await asyncio.open_connection(
                self._host, self._port
            )
            self._mark_connected(True)
            logger.info("Connected to %s:%d", self._host, self._port)
        except Exception as e:
            raise SocketError(f"LAN connect failed: {e}") from e

    async def disconnect(self) -> None:
        try:
            if self._writer:
                self._writer.close()
                await self._writer.wait_closed()
            self._mark_connected(False)
            logger.info("Disconnected from %s:%d", self._host, self._port)
        except Exception as e:
            logger.warning("Disconnect failed: %s", e)

    async def send_command(self, command: str) -> str:
        if not self.connected or not self._writer or not self._reader:
            raise SocketError("Not connected")

        try:
            # コマンド送信（改行で終端）
            self._writer.write((command + "\n").encode())
            await self._writer.drain()

            # 応答受信（行単位）
            response = await self._reader.readline()
            return response.decode().strip()
        except Exception as e:
            raise SocketError(f"LAN send_command failed: {e}") from e

    async def is_alive(self) -> bool:
        """
        ICMP ping による疎通確認。
        """
        if not self._host:
            return False

        if platform.system().lower() == "windows":
            cmd = ["ping", "-n", "1", "-w", "1000", self._host]  # timeout=1s
        else:
            cmd = ["ping", "-c", "1", "-W", "1", self._host]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            returncode = await proc.wait()
            return returncode == 0
        except Exception:
            return False
