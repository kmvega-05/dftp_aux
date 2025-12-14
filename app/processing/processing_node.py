import logging
from random import randint
from app.node_type import NodeType
from app.processing.command import Command
from app.processing.handlers_dispatch import HANDLERS_FTP_COMMANDS
from app.router.FTPSession import FTPSession
from comm.message import Message
from location.location_node import LocationNode

logger = logging.getLogger("dftp.processing.processing_node")

class ProcessingNode(LocationNode):
    def __init__(self, node_name, ip, port, discovery_port = 9100, discovery_timeout = 0.8, heartbeat_interval = 2, node_type = None, discovery_workers = 32):
        super().__init__(node_name, ip, port, discovery_port, discovery_timeout, heartbeat_interval, node_type, discovery_workers)
        self.node_type = NodeType.PROCESSING
        self.register_handler("PROCESS_FTP_COMMAND", self._handle_process_ftp_command)

    def _handle_process_ftp_command(self, message: Message, sock):
        payload = message.payload
        line = payload.get("command")
        command = Command(line)
        if not command:
            return Message(
                type="PROCESS_FTP_RESPONSE",
                src=self.node_name,
                dst=message.header.get("src"),
                payload={
                    "code": 500,
                    "msg": "Invalid command"
                }
            )
        handler = HANDLERS_FTP_COMMANDS.get(command.name)
        if not handler:
            return Message(
                type="PROCESS_FTP_RESPONSE",
                src=self.node_name,
                dst=message.header.get("src"),
                payload={
                    "code": 502,
                    "msg": "Command not implemented"
                }
            )
        # Servicios disponibles para handlers
        #TODO: Aqui extraemos informacion necesaria de los handlers
        client_session = self._rebuild_client_session(payload)
        try:
            code, msg = handler(command, client_session, self)
            result = {
                "code": code,
                "msg": msg
            }
        except Exception:
            logger.exception("Error procesando comando %s", command)
            result = {
                "code": 451,
                "msg": "Requested action aborted"
            }
        return Message(
            type="PROCESS_FTP_RESPONSE",
            src=self.ip,
            dst=message.header.get("src"),
            payload=result
        )
    
    def _rebuild_client_session(self, payload: dict) -> 'FTPSession':
        session = FTPSession()
        session.session_id = payload["session_id"]
        session.current_path = payload["cwd"]
        session.username = payload["username"]
        return session
    
    def get_auth_node(self):
        auth_nodes = self.query_by_role(NodeType.AUTH)
        if not auth_nodes or len(auth_nodes) == 0:
            pass
            #TODO: Agregar error aqui
        index = randint(0, len(auth_nodes) - 1)
        return auth_nodes[index]
    
    def get_data_node(self):
        auth_nodes = self.query_by_role(NodeType.DATA)
        if not auth_nodes or len(auth_nodes) == 0:
            pass
            #TODO: Agregar error aqui
        index = randint(0, len(auth_nodes) - 1)
        return auth_nodes[index]