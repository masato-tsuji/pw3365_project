import abc
import socket
import logging
from typing import Optional


class SocketBase(abc.ABC):
    """
    ソケット通信の抽象基底クラス。
    各サービスでこのクラスを継承して実装する。
    """

    def __init__(self, host: str, port: int, timeout: Optional[int] = 5):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock: Optional[socket.socket] = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def connect(self):
        """サーバーへ接続"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.host, self.port))
            self.logger.info(f"Connected to {self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            raise

    def disconnect(self):
        """接続を閉じる"""
        if self.sock:
            self.sock.close()
            self.sock = None
            self.logger.info("Disconnected")

    @abc.abstractmethod
    def send_command(self, command: str) -> str:
        """
        機器固有のコマンド送信処理を実装する抽象メソッド。
        """
        pass
