#from entities.file_system_manager import _GLOBAL_FSM as fs_manager, SecurityError

from app.processing.command import Command
from app.processing.processing_node import ProcessingNode
from app.router.FTPSession import FTPSession
from comm.message import Message


def handle_mkd(command: 'Command', client_session: 'FTPSession', processing_node: 'ProcessingNode'):
    """Maneja comando MKD - Make Directory (RFC-959).

    Crea un directorio relativo al current_directory del usuario o una ruta
    absoluta dentro del root del usuario.
    """
    # Chequea argumentos
    if not command.require_args(1):
        return 501, "Syntax error in parameters"

    # Valida autenticación
    if not client_session.is_authenticated():
        return 530, "Not logged in"

    new_dir_name = command.get_arg(0)

    # Obtener directorio raíz y actual (resolverá paths virtuales)
    user_root = client_session.root_directory 
    current_directory = client_session.current_path
    ip, port = processing_node.get_data_node()
    msg = Message(type='CHECK_MKD', src=processing_node.ip, dst=ip, payload={'root': user_root, 'current': current_directory, 'dir': new_dir_name})
    # Crea el directorio usando FileSystemManager
    try:
        response = processing_node.send_message(ip, port, msg, True, 2.0)
        msg = response.payload['msg']
    except FileExistsError as e:
        return 550, str(e)
    except Exception as e:
        return 550, str(e)
    except Exception:
        return 451, "Requested action aborted. Local error in processing"

    return 257, msg