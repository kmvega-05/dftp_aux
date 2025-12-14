#from entities.file_system_manager import _GLOBAL_FSM as fs_manager, SecurityError
import os

from app.processing.command import Command
from app.processing.processing_node import ProcessingNode
from app.router.FTPSession import FTPSession
from comm.message import Message


def handle_cdup(command: 'Command',client_session: 'FTPSession', processing_node: 'ProcessingNode'):
    print("CDUP handler called")
    pass
    """Maneja comando CDUP - Change to Parent Directory"""

    # Chequear argumentos
    if not command.require_args(0):
        return 501, "Syntax error in parameters"

    # Verificar autenticación 
    if not client_session.authenticated:
        return 530, "Not logged in"

    # Obtener directorio raiz y actual
    user_root = client_session.root_directory
    current_dir = client_session.current_directory
    ip, port = processing_node.get_data_node()
    msg = Message(type="CHECK_EXISTS", src= processing_node.ip, dst=ip, payload={"root": user_root, "current": current_dir, "absolute": "..", "want": 'dir'})
    response = processing_node.send_message(ip, port, msg, await_response=True, timeout= 2.0)
    try:
        virtual = response.payload.get("path")
    except Exception as e:
        return 550, str(e)
    except FileNotFoundError:
        return 550, "Parent directory not found"
    except NotADirectoryError:
        return 550, "Parent is not a directory"
    return 250, f'Directory changed to "{virtual}"'