from app.processing.command import Command
from app.processing.processing_node import ProcessingNode
from app.router.FTPSession import FTPSession
from comm.message import Message


def handle_dele(command: 'Command', client_session: 'FTPSession', processing_node: 'ProcessingNode'):
    """Maneja comando DELE - Delete file"""

    # Chequear argumentos
    if not command.require_args(1):
        return 501, "Syntax error in parameters"

    # Verificar autenticación
    if not client_session.authenticated:
        return 530, "Not logged in"

    filename = command.get_arg(0)
    user_root = client_session.root_directory
    current_directory = client_session.current_path
    ip, port = processing_node.get_data_node()
    msg = Message(type='CHECK_DELE', src=processing_node.ip, dst=ip, payload={'root': user_root, 'current': current_directory, 'path': filename})
    try:
        response = processing_node.send_message(ip, port, msg, True, 2.0)
        msg = response.payload['msg']
    except FileNotFoundError:
        return 550, "File not found"
    except IsADirectoryError:
        return 550, "Not a file"
    except Exception as e:
        return 550, str(e)
    except Exception:
        return 451, "Requested action aborted. Local error in processing"
    return 250, msg