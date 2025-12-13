import logging
import os

_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

from .message import Message
from .tcp_server import TCPServer
from .tcp_client import TCPClient
from .communication_node import CommunicationNode

__all__ = ["Message", "TCPServer", "TCPClient", "CommunicationNode"]