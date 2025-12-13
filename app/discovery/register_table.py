import threading
from app.discovery import ServiceRegister, NodeType  
import time

class RegisterTable:
    """
    Tabla de nodos registrados en memoria.
    Garantiza thread-safety y evita duplicados por nombre o IP.
    """
    def __init__(self):
        self._nodes: dict[str, ServiceRegister] = {}  # name -> ServiceRegister
        self._ips: set[str] = set()                   # IPs registradas
        self._lock = threading.Lock()                 # Lock para concurrencia

    def _validate_node_type(self, node: ServiceRegister):
        """Valida que el tipo del nodo sea un NodeType válido."""
        if not isinstance(node.node_type, NodeType):
            raise ValueError(
                f"Invalid node type '{node.node_type}'. "
                f"Expected one of: {[t.value for t in NodeType]}"
            )

    def add_node(self, node: ServiceRegister):
        """Agrega o actualiza un nodo en el registro, evitando duplicados por IP."""
        with self._lock:
            # Validación del tipo
            self._validate_node_type(node)

            existing_node = self._nodes.get(node.name)
            if existing_node:
                # Nodo ya existe, actualizamos su IP y tipo si cambió
                if existing_node.ip != node.ip:
                    if node.ip in self._ips:
                        raise ValueError(f"Node IP '{node.ip}' already exists")
                    self._ips.discard(existing_node.ip)
                    self._ips.add(node.ip)
                existing_node.ip = node.ip
                existing_node.node_type = node.node_type
                existing_node.last_heartbeat = time.time()
            else:
                # Nodo nuevo
                if node.ip in self._ips:
                    raise ValueError(f"Node IP '{node.ip}' already exists")
                self._nodes[node.name] = node
                self._ips.add(node.ip)


    def remove_node(self, name: str):
        """Elimina un nodo del registro por su nombre."""
        with self._lock:
            node = self._nodes.pop(name, None)
            if node:
                self._ips.discard(node.ip)

    def get_node(self, name: str) -> ServiceRegister | None:
        """Devuelve el nodo con el nombre dado, o None si no existe."""
        with self._lock:
            return self._nodes.get(name)

    def get_nodes_by_type(self, node_type: NodeType) -> list[ServiceRegister]:
        """Devuelve todos los nodos de un tipo específico."""
        with self._lock:
            return [node for node in self._nodes.values() if node.node_type == node_type]

    def get_all_nodes(self) -> list[ServiceRegister]:
        """Devuelve todos los nodos registrados."""
        with self._lock:
            return list(self._nodes.values())
