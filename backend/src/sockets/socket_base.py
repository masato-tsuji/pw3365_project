# backend/src/utils/socket_base.py
from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class SocketError(Exception):
    """通信全般の例外ベース"""


class SocketNotConnected(SocketError):
    """未接続で操作したとき"""


class SocketBase(ABC):
    """
    すべての通信チャネル（LAN/USBなど）の共通インターフェース基盤クラス。

    実装ポリシー:
      - connect()/disconnect()/send_command()/is_alive() は派生クラスで実装
      - 送受信は request() を経由させると排他制御と接続チェックを自動化できる
      - 非同期コンテキストマネージャ対応（async with 〜）
    """

    def __init__(self, name: str = "", timeout: Optional[float] = 10.0) -> None:
        self._name = name or self.__class__.__name__
        self._timeout = timeout
        self._connected: bool = False
        # 同時送信防止（1リクエスト=1トランザクション）
        self._io_lock = asyncio.Lock()

    # ====== 状態 ======
    @property
    def connected(self) -> bool:
        return self._connected

    def _mark_connected(self, value: bool) -> None:
        self._connected = value

    # ====== ライフサイクル ======
    @abstractmethod
    async def connect(self) -> None:
        """
        物理/論理接続を開始する。
        実装側で成功したら self._mark_connected(True) を呼ぶこと。
        """
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        """
        接続を閉じる。
        実装側でクローズ後に self._mark_connected(False) を呼ぶこと。
        """
        raise NotImplementedError

    # ====== ヘルスチェック ======
    @abstractmethod
    async def is_alive(self) -> bool:
        """
        通信路が生きているかを返す。
        可能なら軽量なNOP/IDNクエリ等で確認する。
        """
        raise NotImplementedError

    # ====== 送受信 ======
    @abstractmethod
    async def send_command(self, command: str) -> str:
        """
        コマンドを送信し、レスポンス（生文字列）を返す。
        ここでは派生クラスが具体実装（TCPやUSB-CDC等）を行う。
        失敗時は適切な例外（SocketError系）を送出すること。
        """
        raise NotImplementedError

    async def request(self, command: str) -> str:
        """
        排他制御＆接続確認つきの高レベル送信API。
        上位層は基本こちらを呼べばOK。
        """
        async with self._io_lock:
            if not self.connected:
                raise SocketNotConnected(f"{self._name} is not connected")
            # タイムアウトが指定されていれば適用
            if self._timeout and self._timeout > 0:
                return await asyncio.wait_for(self.send_command(command), timeout=self._timeout)
            return await self.send_command(command)

    # ====== ユーティリティ ======
    async def ensure_connected(self) -> None:
        """未接続なら connect() する簡易ヘルパー。"""
        if not self.connected:
            await self.connect()

    # ====== async context manager ======
    async def __aenter__(self) -> "SocketBase":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        try:
            await self.disconnect()
        except Exception as e:
            logger.warning("disconnect() failed in __aexit__: %s", e)

