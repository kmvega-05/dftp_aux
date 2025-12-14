#from entities.user_manager import validate_password
from app.processing.command import Command
from app.processing.processing_node import ProcessingNode
from app.router.FTPSession import FTPSession
from comm.message import Message


def handle_pass(command: 'Command', client_session: 'FTPSession', processing_node: 'ProcessingNode'):
    """Maneja comando PASS - validación de contraseña."""
    if not command.require_args(1):
        return 501, "Syntax error in parameters"

    # Verificar que primero se envió USER
    if not client_session.username:
        return 503, "Login with USER first"

    password = command.get_arg(0)
    ip, port = processing_node.get_auth_node()
    msg = Message("CHECK_PASS", processing_node.ip, ip, payload={"username":client_session.username, "password" : password})
    response = processing_node.send_message(ip, port, msg, True, 2.0)
    if response.payload["result"]:
        return 230, "User logged in successfully"
    else:
        return 530, "Not logged in, password incorrect"