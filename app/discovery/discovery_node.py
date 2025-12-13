import ipaddress
import threading
import time
import concurrent.futures
import os
import logging

from comm import Message, CommunicationNode
from app.discovery import RegisterTable, ServiceRegister, NodeType

logger = logging.getLogger("dftp.app.discovery_node")


class DiscoveryNode(CommunicationNode):
    """"Discovery Node
    Nodo que gestiona una tabla de registros de servicios para que otros nodos puedan encontrarse entre ellos.
    La tabla contiene registros de los nodos del sistema incluyendo: Nombre, Ip, Tipo/Rol, Last_Heartbeat
    
    Operaciones sobre DiscoveryNode
    
    - heartbeat: Envia una señal al DiscoveryNode, utilizado para registrar nuevos nodos en la tabla de registros,
        mantener el nodo activo en la tabla y para que otros Discovery Nodes puedan encontrar al actual.
        
    - query_by_name: Consulta un nodo registrado por su nombre.
    
    - query_by_role: Consulta nodos registrados por su rol/tipo.

    - query_all: Consulta todos los nodos registrados.

    Hilos que ejecuta en background:

    - update_discovery_peers_loop: escanea la subred en busca de otros DiscoveryNodes enviando heartbeats periódicos.

    - clean_inactive_register_loop: limpia nodos inactivos de la tabla de registros basándose en timeouts de heartbeat.
    
    """

    def __init__(self, node_name: str, ip: str, port: int, heartbeat_timeout: int = 10, clean_interval: int = 60,
        discovery_interval: int = 10, discovery_timeout: float = 0.8, discovery_workers: int = 32, testing: bool = False):
        
        # Iniciar CommunicationNode para permitir intercambio de mensajes.
        super().__init__(node_name, ip, port)

        # Tabla de servicios registrados
        self.register_table = RegisterTable()

        # Conjunto de discovery Nodes
        self.peers: dict[str, str] = {}
        self.peers_lock = threading.Lock()

        # Configuración de red / scanning
        subnet = os.getenv("DISCOVERY_SUBNET")
        if not subnet:
            raise ValueError("DISCOVERY_SUBNET not set")
        
        self.subnet = subnet
        self.possible_ips = self.get_possible_ips()
        self.discovery_interval = discovery_interval
        self.discovery_timeout = discovery_timeout
        self.discovery_workers = discovery_workers

        # Registros y timeouts
        self.heartbeat_timeout = heartbeat_timeout
        self.clean_interval = clean_interval

        # Registar funciones para manejar distintos tipos de mensajes recibidos.
        self.register_handlers()

        logger.info("DiscoveryNode %s iniciado en %s:%s (subnet=%s)", self.node_name, self.ip, self.port, self.subnet)

        # Hilos de background
        self._stop = threading.Event()
        if not testing:
            # Hilo de descubrimiento de peers
            t1 = threading.Thread(target=self.update_discovery_peers_loop, daemon=True)
            t1.start()

            # Hilo de Limpieza de registros
            t2 = threading.Thread(target=self.clean_inactive_register_loop, daemon=True)
            t2.start()

    # ---------------- Helpers publicos ----------------
    def register_handlers(self):
        """Registra las funciones para manejar los distintos tipos de mensajes recibidos por el protocolo
        de Comunicación"""

        self.register_handler("DISCOVERY_HEARTBEAT", self._handle_heartbeat)
        self.register_handler("DISCOVERY_QUERY_BY_NAME", self._handle_query_by_name)
        self.register_handler("DISCOVERY_QUERY_BY_ROLE", self._handle_query_by_role)
        self.register_handler("DISCOVERY_QUERY_ALL", self._handle_query_all)

    def get_possible_ips(self) -> list[str]:
        """Obtiene todas las posibles ips de hosts de la red exceptuando la ip propia para el envío de mensajes"""
        net = ipaddress.ip_network(self.subnet, strict=False)
        return [str(ip) for ip in net.hosts() if str(ip) != self.ip]

    # ---------------- Handlers obligatorios ----------------
    def _handle_heartbeat(self, message: Message, client_sock):
        """Maneja DISCOVERY_HEARTBEAT:
            . registra/actualiza registro de un nodo del sistema
            . retorna información de contacto del nodo actual para que otros nodos puedan intercambiar mensajes
            . usado para descubrimiento por parte de otros nodos(incluidos otros Discovery Nodes)

        Recibe Message(... payload: { name, ip, role })
        Retorna Message(.. payload: {status, ip, name}) -> del nodo actual
        """
        try:
            payload = message.payload or {}
            name = payload.get("name")
            ip = payload.get("ip")
            role = payload.get("role")
            if not name or not ip or not role:
                return Message(type="DISCOVERY_HEARTBEAT_RESPONSE", src=self.ip, dst=message.header.get("src"), payload={"status": "ERROR", "error_msg": "missing fields", "ip": self.ip, "name": self.node_name})

            # Si quien envía es un discovery node (role == 'DISCOVERY') lo tratamos como peer
            if str(role).upper() == "DISCOVERY":
                return Message(type="DISCOVERY_HEARTBEAT_RESPONSE", src=self.ip, dst=message.header.get("src"), payload={"status": "OK", "ip": self.ip, "name": self.node_name})

            # No es discovery: registrar/actualizar en tabla
            try:
                node_type = NodeType(role)
            except Exception:
                # role inválido, no podemos registrar
                return Message(type="DISCOVERY_HEARTBEAT_RESPONSE", src=self.ip, dst=message.header.get("src"), payload={"status": "ERROR", "error_msg": "invalid role", "ip": self.ip, "name": self.node_name})

            existing = self.register_table.get_node(name)
            if existing:
                # actualizar ip y heartbeat
                existing.ip = ip
                existing.heartbeat()
            else:
                try:
                    sr = ServiceRegister(name, ip, node_type)
                    self.register_table.add_node(sr)
                except Exception as e:
                    logger.exception("Error registrando nodo %s: %s", name, e)
                    return Message(type="DISCOVERY_HEARTBEAT_RESPONSE", src=self.ip, dst=message.header.get("src"), payload={"status": "ERROR", "error_msg": str(e), "ip": self.ip, "name": self.node_name})

            return Message(type="DISCOVERY_HEARTBEAT_RESPONSE", src=self.ip, dst=message.header.get("src"), payload={"status": "OK", "ip": self.ip, "name": self.node_name})

        except Exception as e:
            logger.exception("Error en _handle_heartbeat: %s", e)
            return Message(type="DISCOVERY_HEARTBEAT_RESPONSE", src=self.ip, dst=message.header.get("src"), payload={"status": "ERROR", "error_msg": str(e), "ip": self.ip, "name": self.node_name})

    def _handle_query_by_name(self, message: Message, client_sock):
        """"Obtiene la ip de un nodo dado su nombre"""
        try:
            name = (message.payload or {}).get("name")
            
            if not name:
                return Message(type="DISCOVERY_QUERY_BY_NAME_RESPONSE", src=self.ip, dst=message.header.get("src"), payload={"status": "ERROR", "error_msg": "missing name"})
            
            node = self.register_table.get_node(name)
            
            if not node:
                return Message(type="DISCOVERY_QUERY_BY_NAME_RESPONSE", src=self.ip, dst=message.header.get("src"), payload={"status": "ERROR", "error_msg": "not found"})
            
            return Message(type="DISCOVERY_QUERY_BY_NAME_RESPONSE", src=self.ip, dst=message.header.get("src"), payload={"status": "OK", "ip": node.ip, "node": node.to_dict()})
        
        except Exception as e:
            logger.exception("Error en query_by_name: %s", e)
            return Message(type="DISCOVERY_QUERY_BY_NAME_RESPONSE", src=self.ip, dst=message.header.get("src"), payload={"status": "ERROR", "error_msg": str(e)})

    def _handle_query_by_role(self, message: Message, client_sock):
        """Obtiene una lista de nodos con un rol específico"""
        try:
            role = (message.payload or {}).get("role")
            
            if not role:
                return Message(type="DISCOVERY_QUERY_BY_ROLE_RESPONSE", src=self.ip, dst=message.header.get("src"), payload={"status": "ERROR", "error_msg": "missing role"})
            
            try:
                node_type = NodeType(role)
            
            except Exception:
                return Message(type="DISCOVERY_QUERY_BY_ROLE_RESPONSE", src=self.ip, dst=message.header.get("src"), payload={"status": "ERROR", "error_msg": "invalid role"})
            
            nodes = self.register_table.get_nodes_by_type(node_type)
            ips = [n.ip for n in nodes]
            
            return Message(type="DISCOVERY_QUERY_BY_ROLE_RESPONSE", src=self.ip, dst=message.header.get("src"), payload={"status": "OK", "ips": ips})
        
        except Exception as e:
            logger.exception("Error en query_by_role: %s", e)
            return Message(type="DISCOVERY_QUERY_BY_ROLE_RESPONSE", src=self.ip, dst=message.header.get("src"), payload={"status": "ERROR", "error_msg": str(e)})

    def _handle_query_all(self, message: Message, client_sock):
        """Obtiene todos los nodos registrados en la tabla"""
        try:
            nodes = self.register_table.get_all_nodes()
            return Message(type="DISCOVERY_QUERY_ALL_RESPONSE", src=self.ip, dst=message.header.get("src"), payload={"status": "OK", "nodes": [n.to_dict() for n in nodes]})
        
        except Exception as e:
            logger.exception("Error en query_all: %s", e)
            return Message(type="DISCOVERY_QUERY_ALL_RESPONSE", src=self.ip, dst=message.header.get("src"), payload={"status": "ERROR", "error_msg": str(e)})

    # ---------------- Background loops ----------------
    def update_discovery_peers_loop(self):
        """Escanea la subred en paralelo enviando DISCOVERY_HEARTBEAT y 
            actualiza self.peers si hay cambios."""

        logger.info("%s: iniciando update_discovery_peers_loop", self.node_name)
        while not self._stop.is_set():
            try:
                found = {}
                results = self._find_peers_in_parallel()

                for _ , response in results:
                    if not response:
                        continue
                    try:
                        peer_name, peer_ip = self._process_peer_discovey_response(response)
                        found[peer_name] = peer_ip

                    except Exception:
                        continue

                self._update_peers(found)

                time.sleep(self.discovery_interval)

            except Exception:
                logger.exception("Error en update_discovery_peers_loop")
                time.sleep(self.discovery_interval)

    def clean_inactive_register_loop(self):
        logger.info("%s: iniciando clean_inactive_register_loop", self.node_name)
        while not self._stop.is_set():
            try:
                time.sleep(self.clean_interval)
                now = time.time()
                dead = [n.name for n in self.register_table.get_all_nodes() if now - n.last_heartbeat > self.heartbeat_timeout]
                
                for name in dead:
                    logger.info("%s: eliminando nodo inactivo %s", self.node_name, name)
                    self.register_table.remove_node(name)
            
            except Exception:
                logger.exception("Error en clean_inactive_register_loop")
                time.sleep(self.clean_interval)

    def _find_peers_in_parallel(self):
        """Envía señales en paralelo a toda la red para encontrar otros Discovery Nodes"""
        max_workers = min(self.discovery_workers, max(1, len(self.possible_ips)))
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = [ex.submit(self._probe_send_heartbeat, ip) for ip in self.possible_ips]
            for fut in concurrent.futures.as_completed(futures):
                try:
                    res = fut.result(timeout=self.discovery_timeout + 0.5)
                except Exception:
                        res = (None, None)
                results.append(res)

        return results

    def _probe_send_heartbeat(self, ip_addr: str):
        """Envía un DISCOVERY_HEARTBEAT a ip_addr; devuelve (ip, response)"""
        try:
            msg = Message(type="DISCOVERY_HEARTBEAT", src=self.ip, dst=ip_addr, payload={"name": self.node_name, "ip": self.ip, "role": "DISCOVERY"})
            resp = self.send_message(ip_addr, self.port, msg, await_response=True, timeout=self.discovery_timeout)
            return ip_addr, resp
        except Exception:
            return ip_addr, None

    def _process_peer_discovey_response(self, response): 
        """Obtiene el nombre y direccion ip de un peer de una respuesta de heartbeat"""
        if response.header.get("type") == "DISCOVERY_HEARTBEAT_RESPONSE" and response.payload.get("status") == "OK":
            peer_name = response.payload.get("name")
            peer_ip = response.payload.get("ip")

            if peer_name and peer_ip:
                return peer_name, peer_ip
            
        raise Exception("Invalid heartbeat response")
    
    def _update_peers(self, found):
        """Actualiza la lista de peers si hay cambios"""
        with self.peers_lock:
            if set(found.items()) != set(self.peers.items()):
                self.peers = found
        

