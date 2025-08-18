# Placeholder for test_socket_base.py
from src.sockets.socket_base import SocketError, SocketNotConnected

def test_socket_exceptions():
    assert issubclass(SocketNotConnected, SocketError)
