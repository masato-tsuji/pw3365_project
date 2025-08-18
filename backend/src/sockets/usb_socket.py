# backend/src/sockets/usb_socket.py
import asyncio
import logging
import serial_asyncio as pyserial_asyncio
from src.sockets.socket_base import SocketBase, SocketError
logger = logging.getLogger(__name__)
class UsbSocket(SocketBase):
    """USB-CDC 通信実装クラス"""
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0):
        super().__init__(name=f"USB({port})", timeout=timeout)
        self._port = port
        self._baudrate = baudrate
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
    async def connect(self) -> None:
        try:
            self._reader, self._writer = await pyserial_asyncio.open_serial_connection(
                url=self._port, baudrate=self._baudrate
            )
            self._mark_connected(True)
            logger.info("USB connected: %s", self._port)
        except Exception as e:
            raise SocketError(f"USB connect failed: {e}") from e
    async def disconnect(self) -> None:
        try:
            if self._writer:
                self._writer.close()
                await self._writer.wait_closed()
            self._mark_connected(False)
            logger.info("USB disconnected: %s", self._port)
        except Exception as e:
            logger.warning("USB disconnect failed: %s", e)
    async def send_command(self, command: str) -> str:
        if not self.connected or not self._writer or not self._reader:
            raise SocketError("USB not connected")
        try:
            self._writer.write((command + "\n").encode())
            await self._writer.drain()
            response = await self._reader.readline()
            return response.decode().strip()
        except Exception as e:
            raise SocketError(f"USB send_command failed: {e}") from e
    async def is_alive(self) -> bool:
        """USBデバイスが接続されているか簡易チェック"""
        return self.connected
