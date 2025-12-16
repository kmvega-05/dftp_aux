import datetime
import uuid
import logging

logger = logging.getLogger("dftp.routing.routing_node")

class FTPSession:
    def __init__(self, client_addr):
        self.session_id = str(uuid.uuid4())
        self.client_addr = client_addr

        self.username = None
        self.authenticated = False
        self.current_path = "/"
        self.root_directory = None
        self.crated_at = datetime.datetime.now()

        self.version: int = 1

        #Cosas Extras
        self.active_transfers = {}
        self.rename_from_path = None

        # PASV / data connection state
        self.data_node_ip = None
        self.data_port = None
        self.pasv_mode = False

    def request_quit(self) -> bool:
        """Marcar la sesión para cierre (QUIT). Retorna True si no hay
        transferencias activas y el servidor puede cerrar la conexión de
        control inmediatamente. Si hay transferencias activas, setea
        `pending_quit` y retorna False.
        """
        #with self.lock:
        self.pending_quit = True
        has_transfers = len(self.active_transfers) > 0
        return not has_transfers
    
    def set_rename_from(self, path: str):
        """Registra el path origen para la operación RNFR."""
        #with self.lock:
        self.rename_from_path = path

    def get_rename_from(self):
        """Devuelve el path registrado por RNFR o None."""
        #with self.lock:
        return self.rename_from_path

    def clear_rename_from(self):
        """Limpia el estado de RNFR."""
        #with self.lock:
        self.rename_from_path = None

    def set_pasv(self, data_node_ip, data_port: int):
        """Configura la información PASV para la sesión."""
        #with self.lock:
        self.data_node_ip = data_node_ip
        self.data_port = data_port
        self.pasv_mode = True
        logger.info("PASV listening on port %s for %s", data_port, self.client_addr)

    def get_pasv_info(self):
        """Retorna (data_socket, data_port) o (None, None)."""
        #with self.lock:
        return self.data_node_ip, self.data_port

    def cleanup_pasv(self):
        """Cierra y limpia la conexión PASV si existe."""
        # with self.lock:
        #     if self.data_socket:
        #         try:
        #             self.data_socket.close()
        #             logger.info("Data socket closed for %s", self.client_address)
        #         except Exception as e:
        #             logger.exception("Error closing data socket: %s", e)
        # self.data_socket = None
        self.data_port = None
        self.pasv_mode = False
        logger.debug("PASV state cleaned up for %s", self.client_addr)