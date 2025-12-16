from app.processing.command import Command
from app.processing.processing_node import ProcessingNode
from app.router.FTPSession import FTPSession
from comm.message import Message


def handle_retr(command: Command, client_session: FTPSession, processing_node: ProcessingNode):
    if not client_session.authenticated:
        return 530, "Not logged in"

    if not command.require_args(1):
        return 501, "Syntax error in parameters"

    if not client_session.pasv_mode:
        return 425, "Use PASV first"

    filename = command.get_arg(0)
    data_node_ip, data_node_port = processing_node.get_data_node()

    msg = Message(
        type="DATA_RETR",
        src=processing_node.ip,
        dst=data_node_ip,
        payload={
            "session_id": client_session.session_id,
            "root": client_session.root_directory,
            "current": client_session.current_path,
            "path": filename
        }
    )

    processing_node.send_message(data_node_ip, data_node_port, msg, False)
    return 226, "Transfer complete"
