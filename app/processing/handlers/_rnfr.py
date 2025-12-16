from app.processing.command import Command
from app.processing.processing_node import ProcessingNode
from app.router.FTPSession import FTPSession
from comm.message import Message


def handle_rnfr(command: 'Command', client_session: 'FTPSession', processing_node: 'ProcessingNode'):
    """Maneja comando RNFR - Rename From"""

    # Chequear argumentos
    if not command.require_args(1):
        return 501, "Syntax error in parameters or arguments"

    # Validar autenticación
    if not client_session.is_authenticated():
        return 530, "Not logged in"

    old_path = command.get_arg(0)
    user_root = client_session.root_directory
    current_dir = client_session.current_path

    ip, port = processing_node.get_data_node()
    msg = Message(type='CHECK_EXISTS', src=processing_node.ip, dst=ip, payload={'root': user_root, 'current': current_dir, 'path': old_path})
    try:
        response = processing_node.send_message(ip, port, msg, True, 2.0)
    except Exception as e:
        return 550, str(e)
    except FileNotFoundError:
        return 550, "File or directory not found"

    # Guardar la ruta virtual para el siguiente RNTO
    client_session.set_rename_from(response['path'])
    return 350, "Ready for destination name"
