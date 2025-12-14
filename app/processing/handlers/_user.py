# from entities.user_manager import user_exists


from app.processing.processing_node import ProcessingNode
from app.router.FTPSession import FTPSession
from comm.message import Message


def handle_user(command, client_session: 'FTPSession', processing_node : 'ProcessingNode'):
    pass
    """Maneja comando USER - autenticación de usuario."""
    if not command.require_args(1):
        return 501, "Syntax error in parameters"
        return

    username = command.get_arg(0)

    # Verificar si el usuario existe usando user_manager
    ip, port = processing_node.get_auth_node()
    msg = Message("CHECK_USER", processing_node.ip, ip, payload={"username":username})
    response = processing_node.send_message(ip, port, msg, True, 2.0)
    if response.payload["result"]:
        return 331, "User name okay, need password"
    else:
        return 530, "User not found"