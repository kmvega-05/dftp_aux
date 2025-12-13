import os
import threading
import time
import ipaddress
import logging
import concurrent.futures

from comm import CommunicationNode, Message
from app.discovery import NodeType

logger = logging.getLogger("dftp.location.location_node")

class LocationNode(CommunicationNode):
    """
    Nodo base para TODOS los nodos del sistema (routing, auth, data, processing).
    Añade:
    - Descubrimiento automático de DiscoveryNodes por subred.
    - Heartbeat periódico hacia los DiscoveryNodes detectados.
    - API simple para consultar discovery: register, query, resolve...
    """

    def __init__(self, node_name: str, ip: str, port: int, discovery_port: int = 9100, discovery_timeout: float = 0.8,
        heartbeat_interval: int = 2, node_type: NodeType = None, discovery_workers: int = 32):
        
        super().__init__(node_name, ip, port)

        # Configuraciones
        self.discovery_port = discovery_port
        self.discovery_timeout = discovery_timeout
        self.heartbeat_interval = heartbeat_interval
        self.node_type = node_type

        self.subnet = os.getenv("DISCOVERY_SUBNET")
        if not self.subnet:
            raise ValueError("DISCOVERY_SUBNET no está configurado en LocationNode")
        
        self.possible_ips = self._get_possible_ips()
        
        # Para scaneo de red paralelo
        self.discovery_workers = discovery_workers

        # Lista de DiscoveryNodes detectados (name -> ip)
        self.discovery_nodes: dict[str, str] = {}
        self.discovery_nodes_lock = threading.Lock()

        logger.info("LocationNode '%s' iniciado en %s:%s (subnet=%s)", self.node_name, self.ip, self.port, self.subnet)

        # ---- Hilos internos ----
        # send_heartbeat_loop envia heartbeats periódicos a los discovery nodes
        self.heartbeat_thread = threading.Thread(target=self._send_heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()


    def _get_possible_ips(self) -> list[str]:
        """Obtiene todas las posibles ips de hosts de la red exceptuando la ip propia para el envío de mensajes"""
        net = ipaddress.ip_network(self.subnet, strict=False)
        return [str(ip) for ip in net.hosts() if str(ip) != self.ip]

    def _get_discovery_node(self) -> str | None:
        with self.discovery_nodes_lock:
            if not self.discovery_nodes:
                return None
            
            return next(iter(self.discovery_nodes.values()))
        
    def query_by_name(self, name: str):
        """
        DISCOVERY_QUERY_BY_NAME
        """
        d_ip = self._get_discovery_node()
        if not d_ip:
            return None

        msg = Message(type="DISCOVERY_QUERY_BY_NAME", src=self.ip, dst=d_ip, payload={"name": name})

        return self.send_message(d_ip, self.discovery_port, msg, await_response=True)

    def query_by_role(self, node_type: NodeType):
        """ DISCOVERY_QUERY_BY_ROLE """
        d_ip = self._get_discovery_node()
        if not d_ip:
            return None

        msg = Message(type="DISCOVERY_QUERY_BY_ROLE", src=self.ip, dst=d_ip, payload={"role": node_type.value})

        return self.send_message(d_ip, self.discovery_port, msg, await_response=True)
        
    def _send_heartbeat_loop(self):
        """Envía heartbeats en paralelo a todas las IPs de la subred para descubrir discovery nodes.

        .Si el nodo no se encuentra registrado en el discovery node este lo registrará automáticamente.
        .Si ya se encontraba registrado simplemente se actualizará su heartbeat e ip."""

        logger.info("[%s] Iniciando send_heartbeat_loop", self.node_name)

        while True:
            try:
                found = self._find_discovery_nodes_in_parallel()

                self._update_discovery_nodes(found)
                time.sleep(self.heartbeat_interval)

            except Exception:
                logger.exception("Error en send_heartbeat_loop")
                time.sleep(self.heartbeat_interval)
    
    def _find_discovery_nodes_in_parallel(self):
        max_workers = min(self.discovery_workers, max(1, len(self.possible_ips)))
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = [ex.submit(self._probe_heartbeat_ip, ip) for ip in self.possible_ips]
            
            for fut in concurrent.futures.as_completed(futures):
                try:
                    res = fut.result(timeout=self.discovery_timeout + 0.5)
                
                except Exception:
                    res = (None, None)
                
                results.append(res)

        return self._collect_heartbeated_nodes(results)

    def _probe_heartbeat_ip(self, ip_addr: str):
        """Envía un DISCOVERY_HEARTBEAT a ip_addr y devuelve (ip, response) o (ip, None)."""
        try:
            payload = {"name": self.node_name, "ip": self.ip, "role": (self.node_type.value if self.node_type else None)}
            msg = Message(type="DISCOVERY_HEARTBEAT", src=self.ip, dst=ip_addr, payload=payload)
            resp = self.send_message(ip_addr, self.discovery_port, msg, await_response=True, timeout=self.discovery_timeout)
            return ip_addr, resp
        
        except Exception:
            return ip_addr, None

    def _collect_heartbeated_nodes(self, results):
        """Construye dict name->ip a partir de iterable de tuplas (ip, response) de heartbeats."""
        found = {}
        for _ , response in results:
            
            if not response:
                continue

            try:
                if response.payload.get("status") == "OK":
                    name = response.payload.get("name")
                    ip = response.payload.get("ip")
                    
                    if name and ip:
                        found[name] = ip

            except Exception:
                continue

        return found

    def _update_discovery_nodes(self, found: dict) -> dict:
        """Actualiza self.discovery_nodes si cambió."""
        with self.discovery_nodes_lock:
            if set(found.items()) != set(self.discovery_nodes.items()):
                self.discovery_nodes = found
