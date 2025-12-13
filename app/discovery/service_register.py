import time
from enum import Enum

class NodeType(Enum):
    ROUTING = "ROUTING"
    PROCESSING = "PROCESSING"
    DATA = "DATA"
    AUTH = "AUTH"

class ServiceRegister:
    """
    Representa un nodo registrado en el DiscoveryNode.
    """
    def __init__(self, name: str, ip: str, node_type: NodeType):
        self.name = name
        self.ip = ip
        self.node_type = node_type
        self.last_heartbeat = time.time()

    def heartbeat(self):
        """
        Actualiza el timestamp del último heartbeat recibido.
        """
        self.last_heartbeat = time.time()

    def to_dict(self) -> dict:
        """
        Devuelve una representación serializable del nodo.
        """
        return {
            "name": self.name,
            "ip": self.ip,
            "type": self.node_type.value,
            "last_heartbeat": self.last_heartbeat
        }

    def __str__(self):
        return f"{self.name} ({self.node_type.value}) - {self.ip}"

    def __eq__(self, other):
        if not isinstance(other, ServiceRegister):
            return False
        return self.ip == other.ip and self.name == other.name

    def __hash__(self):
        return hash((self.name, self.ip))
