from app.processing.command import Command
from app.processing.processing_node import ProcessingNode
from app.router.FTPSession import FTPSession


def handle_pwd(command: 'Command', client_session: 'FTPSession', processing_node: 'ProcessingNode'):
    """Maneja comando PWD - Print Working Directory"""

    # Chequear argumentos
    if not command.require_args(0):
        return 501, "Syntax error in parameters"

    # Verificar autenticación
    if not client_session.authenticated:
        return 530, "Not logged in"

    # Obtener el directorio actual de la sesión
    current_dir = client_session.current_path

    # Enviar respuesta en formato FTP (257 "PATHNAME")
    return 257, f'"{current_dir}" is the current directory'