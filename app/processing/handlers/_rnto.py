#from entities.file_system_manager import _GLOBAL_FSM as fs_manager, SecurityError


from app.processing.command import Command
from app.processing.processing_node import ProcessingNode
from app.router.FTPSession import FTPSession
from comm.message import Message


def handle_rnto(command: 'Command', client_session: 'FTPSession', processing_node: 'ProcessingNode'):
    """Maneja comando RNTO - Rename To (rename target path)."""
    # 1. Autenticación
    if not client_session.authenticated():
        return 530, "Not logged in"

    # 2. Validar argumentos
    if not command.require_args(1):
        return 501, "Syntax error in parameters"

    # 3. Verificar que se haya ejecutado RNFR previamente
    old_virtual_path = client_session.get_rename_from()
    if not old_virtual_path:
        return 503, "RNFR required first"

    # 4. Obtener el nuevo path dado por el usuario
    requested_new_path = command.get_arg(0)
    user_root = client_session.root_directory 
    current_dir = client_session.current_directory
    ip, port = processing_node.get_data_node()
    msg = Message(type='CHECK_RNTO', src=processing_node.ip, dst=ip, payload={'root': user_root, 'current': current_dir, 'old': old_virtual_path, 'new': requested_new_path})
    try:
        processing_node.send_message(ip, port, msg, True, 2.0)
    except Exception as e:
        client_session.clear_rename_from()
        return 550, str(e)
    except Exception:
        client_session.clear_rename_from()
        return 451, "Requested action aborted. Local error in processing"

    client_session.clear_rename_from()
    return 250, f'"{old_virtual_path}" renamed to "{requested_new_path}"'