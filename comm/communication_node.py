import logging
from comm import Message, TCPServer, TCPClient

logger = logging.getLogger("dftp.comm.communication_node")

class CommunicationNode:
    def __init__(self, node_name: str, ip: str, port: int):
        """
        node_name: identificador del nodo
        ip, port: dirección donde el nodo escucha
        """
        self.node_name = node_name
        self.ip = ip
        self.port = port
        self.handlers = {}  # type -> callback(Message, socket) -> Message | None

        # Instancia TCPServer y TCPClient
        self.server = TCPServer(ip, port, self._on_message)
        self.client = TCPClient()
        self.start_server()

    # ---------------- Métodos públicos ----------------
    def start_server(self):
        """Inicia el servidor TCP para recibir mensajes."""
        self.server.start()

    def stop_server(self):
        """Detiene el servidor TCP."""
        self.server.stop()
        logger.info("Server stopped on %s:%s", self.ip, self.port)

    def connect_to(self, dst_ip: str, dst_port: int):
        """
        Placeholder para futuras conexiones persistentes.
        Actualmente TCPClient conecta en cada send_message.
        """
        logger.debug("Preparado para conectar a %s:%s", dst_ip, dst_port)

    def send_message(self, ip, port, msg, await_response=True, timeout=1.0):
        # Evitar logs muy verbosos en la ruta caliente; DEBUG si se necesita traza
        logger.debug("Enviando mensaje a %s:%s tipo=%s src=%s dst=%s", ip, port, msg.header.get("type"), msg.header.get("src"), msg.header.get("dst"))
        response = self.client.send_message(ip, port, msg, await_response, timeout=timeout)
        logger.debug("Respuesta recibida de %s:%s -> %s", ip, port, getattr(response, "header", None))
        return response


    def register_handler(self, type: str, callback):
        """
        Registra un callback para un tipo de mensaje específico.
        callback: función que recibe (Message, socket) y devuelve Message o None
        """
        self.handlers[type] = callback
        logger.debug("Handler registrado para tipo '%s' en nodo %s", type, self.node_name)

    # ---------------- Métodos internos ----------------
    def _on_message(self, message: Message, client_sock):
        """Callback interno que recibe mensajes del TCPServer."""
        handler = self.handlers.get(message.header['type'])
        if handler:
            response = handler(message, client_sock)
            return response
        else:
            logger.debug("No hay handler para tipo '%s'", message.header['type'])
            return None
