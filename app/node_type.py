from enum import Enum

class NodeType(Enum):
    ROUTING = "ROUTING"
    PROCESSING = "PROCESSING"
    DATA = "DATA"
    AUTH = "AUTH"