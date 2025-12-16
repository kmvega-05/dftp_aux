import logging
import socket
import threading
from app.node_type import NodeType
from app.router.FTPSession import FTPSession
from comm.message import Message
from location.location_node import LocationNode

logger = logging.getLogger("dftp.routing.routing_node")


DATA_COMMANDS = {"LIST", "NLIST", "RETR", "STOR", "STOU"}


class RoutingNode(LocationNode):
    """
    RoutingNode:
    - Maneja conexión de control FTP
    - Mantiene estado de sesión
    - Orquesta Processing / Data
    """

    def __init__(
        self,
        node_name: str,
        ip: str,
        ftp_port: int = 21,
        internal_port: int = 9000,
        discovery_port: int = 9100,
    ):
        super().__init__(
            node_name=node_name,
            ip=ip,
            port=internal_port,
            discovery_port=discovery_port,
            node_type=NodeType.ROUTING,
        )

        self.ftp_port = ftp_port
        self.sessions: dict[str, FTPSession] = {}
        self.sessions_lock = threading.Lock()

        self.ftp_server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ftp_server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.ftp_server_sock.bind((self.ip, self.ftp_port))
        self.ftp_server_sock.listen(50)

        logger.info(
            "[RoutingNode %s] FTP escuchando en %s:%s",
            self.node_name,
            self.ip,
            self.ftp_port,
        )

        threading.Thread(
            target=self._accept_clients_loop,
            daemon=True,
        ).start()

    # ------------------------------------------------------------------ #

    def _accept_clients_loop(self):
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

    # ------------------------------------------------------------------ #

    def _handle_client_session(self, client_sock, session: FTPSession, addr):
        buffer = ""
        try:
            self.send_response_to_client(
                client_sock, 220, "Distributed FTP Server Ready", addr
            )

            while True:
                data = client_sock.recv(1024)
                if not data:
                    break

                buffer += data.decode()
                while "\r\n" in buffer:
                    line, buffer = buffer.split("\r\n", 1)
                    line = line.strip()
                    if not line:
                        continue

                    logger.debug("[SESSION %s] <- %s", session.session_id, line)

                    # Comandos locales
                    cmd = line.split()[0].upper()

                    if cmd == "QUIT":
                        self.send_response_to_client(
                            client_sock, 221, "Goodbye", addr
                        )
                        return

                    code, msg = self._handle_ftp_command(session, line)

                    # 150 se manda ANTES si hay transferencia
                    if cmd in DATA_COMMANDS and code == 226:
                        self.send_response_to_client(
                            client_sock, 150, "Opening data connection", addr
                        )

                    self.send_response_to_client(client_sock, code, msg, addr)

        except Exception:
            logger.exception("Error en sesión %s", session.session_id)

        finally:
            self._close_session(session)
            try:
                client_sock.close()
            except Exception:
                pass

    # ------------------------------------------------------------------ #

    def _handle_ftp_command(self, session: FTPSession, line: str):
        processing_node = self._select_processing_node()
        if not processing_node:
            return 421, "No processing service available"

        payload = {
            "session_id": session.session_id,
            "command": line,
            "username": session.username,
            "cwd": session.current_path,
            "client_ip": session.client_addr[0],
        }

        msg = Message(
            type="PROCESS_FTP_COMMAND",
            src=self.ip,
            dst=processing_node.ip,
            payload=payload,
        )

        resp = self.send_message(
            processing_node.ip,
            processing_node.port,
            msg,
            await_response=True,
            timeout=5.0,
        )

        if not resp:
            return 450, "Processing error"

        return self._apply_processing_response(session, resp)

    # ------------------------------------------------------------------ #

    def _apply_processing_response(self, session: FTPSession, resp: Message):
        payload = resp.payload
        code = payload.get("code", 500)
        msg = payload.get("msg", "")

        # 🔹 Actualización de estado de sesión
        if payload.get("authenticated") is True:
            session.authenticated = True
            session.username = payload.get("username")

        if "cwd" in payload:
            session.current_path = payload["cwd"]

        return code, msg

    # ------------------------------------------------------------------ #

    def _select_processing_node(self):
        resp = self.query_by_role(NodeType.PROCESSING)
        if not resp or not resp.payload:
            return None
        nodes = resp.payload.get("nodes", [])
        if not nodes:
            return None
        return nodes[0]

    # ------------------------------------------------------------------ #

    def _close_session(self, session: FTPSession):
        logger.info("Cerrando sesión %s", session.session_id)
        with self.sessions_lock:
            self.sessions.pop(session.session_id, None)

    # ------------------------------------------------------------------ #

    def send_response_to_client(self, client_socket, code: int, message: str, addr):
        try:
            line = f"{code} {message}\r\n"
            client_socket.sendall(line.encode("utf-8"))
            logger.debug("-> %s %s", addr, line.strip())
        except Exception:
            logger.exception("Error enviando respuesta FTP")
