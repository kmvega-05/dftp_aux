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
        self.crated_at = datetime.datetime.now()

        self.version: int = 1

        #Cosas Extras
        self.active_transfers = {}

    def request_quit(self) -> bool:
        """Marcar la sesión para cierre (QUIT). Retorna True si no hay
        transferencias activas y el servidor puede cerrar la conexión de
        control inmediatamente. Si hay transferencias activas, setea
        `pending_quit` y retorna False.
        """
        with self.lock:
            self.pending_quit = True
            has_transfers = len(self.active_transfers) > 0
            return not has_transfers