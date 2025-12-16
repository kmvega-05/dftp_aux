#from entities.file_system_manager import _GLOBAL_FSM as fs_manager, SecurityError

from app.processing.command import Command
from app.processing.processing_node import ProcessingNode
from app.router.FTPSession import FTPSession
from comm.message import Message


def handle_rmd(command: 'Command', client_session: 'FTPSession', processing_node: 'ProcessingNode'):
    """Maneja comando RMD - Remove Directory (RFC-959)."""

    # Chequea argumentos
    if not command.require_args(1):
        return 501, "Syntax error in parameters"

    # Valida autenticación
    if not client_session.authenticated:
        return 530, "Not logged in"

    dir_name = command.get_arg(0)

    # Obtener directorio raíz y actual
    user_root = client_session.root_directory
    current_directory = client_session.current_path
    ip, port = processing_node.get_data_node()
    msg = Message(type='CHECK_RMD', src=processing_node.ip, dst=ip, payload={'root': user_root, 'current': current_directory, 'dir': dir_name})
    try:
        response = processing_node.send_message(ip, port, msg, True, timeout=2.0)
        msg = response.payload['msg']
    except FileNotFoundError:
        return 550, "Directory does not exist"
    except NotADirectoryError:
        return 550, "Not a directory"
    except OSError as e:
        # Directory not empty or other OS errors
        return 550, str(e)
    except Exception as e:
        return 550, str(e)

    return 250, msg