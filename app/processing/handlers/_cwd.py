import os
from app.processing.command import Command
from app.processing.processing_node import ProcessingNode
from app.router.FTPSession import FTPSession
from comm.message import Message


def handle_cwd(command: 'Command', client_session: 'FTPSession', processing_node: 'ProcessingNode'):
    """Maneja comando CWD - Change Working Directory"""

    # Chequear argumentos
    if not command.require_args(1):
        return 501, "Syntax error in parameters"

    # Verificar autenticación
    if not client_session.is_authenticated():
        return 530, "Not logged in"

    new_directory = command.get_arg(0)

    # Obtener directorio raíz y actual
    user_root = client_session.root_directory
    current_dir = client_session.current_path
    ip, port = processing_node.get_data_node()
    msg = Message(type="CHECK_EXISTS", src= processing_node.ip, dst=ip, payload={"root": user_root, "current": current_dir, "path": new_directory, "want": 'dir'})
    try:
        response = processing_node.send_message(ip, port, msg, await_response=True, timeout= 2.0)
        virtual = response.payload.get("path")
    except Exception as e:
        return 550, str(e)
    except FileNotFoundError:
        return 550, "Directory not found"
    except NotADirectoryError:
        return 550, "Not a directory"

    client_session.current_path = virtual
    return 250, f'Directory changed to "{virtual}"'