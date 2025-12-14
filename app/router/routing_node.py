import logging
import socket
import threading
from app.node_type import NodeType
from app.router.FTPSession import FTPSession
from comm.message import Message
from location.location_node import LocationNode

logger = logging.getLogger("dftp.routing.routing_node")

class RoutingNode(LocationNode):
    """
    RoutingNode:
    - Acepta conexiones FTP (RFC959)
    - Mantiene estado de sesión
    - Rutea comandos a ProcessingNodes
    """
    def __init__(self,node_name: str,ip: str,ftp_port: int = 21,internal_port: int = 9000,discovery_port: int = 9100):
        super().__init__(node_name=node_name, ip=ip, port=internal_port, discovery_port=discovery_port, node_type=NodeType.ROUTING)

        # Puerto FTP
        self.ftp_port = ftp_port
        self.sessions: dict[str, FTPSession] = {}
        self.sessions_lock = threading.Lock()

        # Socket FTP
        self.ftp_server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ftp_server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.ftp_server_sock.bind((self.ip, self.ftp_port))
        self.ftp_server_sock.listen(50)
        logger.info( "[RoutingNode %s] FTP escuchando en %s:%s", self.node_name, self.ip, self.ftp_port)

        self.accept_thread = threading.Thread(target=self._accept_clients_loop, daemon=True)
        self.accept_thread.start()

    def _accept_clients_loop(self):
        logger.info("[%s] Accept loop FTP iniciado", self.node_name)
        while True:
            try:
                client_sock, client_addr = self.ftp_server_sock.accept()
                logger.info("Cliente FTP conectado desde %s", client_addr)
                session = FTPSession(client_addr)
                with self.sessions_lock:
                    self.sessions[session.session_id] = session
                threading.Thread(
                    target=self._handle_client_session,
                    args=(client_sock, session, client_addr),
                    daemon=True,
                ).start()
            except Exception:
                logger.exception("Error aceptando cliente FTP")

    def _handle_client_session(self, client_sock: 'socket.socket', session: FTPSession, addres):
        buffer = ""
        try:
            #session.send_response("220 Distributed FTP Server Ready")
            self.send_response_to_client(client_sock, 220, "Distributed FTP Server Ready", addres)
            while True:
                data = client_sock.recv(1024)
                if not data:
                    break
                buffer += data.decode()
                while "\r\n" in buffer:
                    line, buffer = buffer.split("\r\n", 1)
                    logger.debug("[SESSION %s] <- %s", session.session_id, line)
                    code, msg = self._handle_ftp_command(session, line)
                    self.send_response_to_client(client_sock, code, msg, addres)
        except Exception:
            logger.exception("Error en sesión %s", session.session_id)
        finally:
            self._close_session(session)

    def _handle_ftp_command(self, session: FTPSession, line: str) -> tuple[int, str]:
        processing_node = self._select_processing_node()
        if not processing_node:
            return 421, "No processing service available"
        with self.sessions_lock:
            payload = {
                "session_id": session.session_id,
                "command": line,
                "user": session.username,
                "cwd": session.current_path,
            }

        msg = Message(
            type="PROCESS_FTP_COMMAND",
            src=self.ip,
            dst=processing_node.ip,
            payload=payload,
        )

        resp = self.send_message(processing_node.ip, processing_node.port, msg, await_response=True, timeout=2.0)
        if not resp:
            return 450, "Processing Error"
        
        return self._parse_response(resp)

    def _select_processing_node(self):
        resp = self.query_by_role(NodeType.PROCESSING)
        if not resp or not resp.payload:
            return None
        nodes = resp.payload.get("nodes", [])
        if not nodes:
            return None
        return nodes[0]

    def _close_session(self, session: FTPSession):
        logger.info("Cerrando sesión %s", session.session_id)
        with self.sessions_lock:
            self.sessions.pop(session.session_id, None)
        session.close()

    def send_response_to_client(self, client_socket: "socket.socket", code: int, message: str, addres) -> None:
        """Envía una respuesta al cliente por `client_socket` con formato RFC-959.

        Esta ayuda centraliza el envío y el logging. No lanza excepciones al llamar.
        """
        try:
            line = f"{code} {message}\r\n"
            # Serializar envíos en la conexión de control
            client_socket.sendall(line.encode('utf-8'))
            logger.info("Sent response to %s: %s", addres, line.strip())
        except Exception:
            logger.exception("Failed to send response to %s: %s", addres, line)
    
    def _parse_response(self, resp: Message):
        code = resp.payload.get("code", 0)
        msg = resp.payload.get("msg", "")
        return code, msg