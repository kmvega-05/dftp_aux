from app.processing.command import Command
from app.router.FTPSession import FTPSession


def handle_noop(command: 'Command', client_session: 'FTPSession', processing_node) -> tuple[int, str]:
    """Maneja comando NOOP - no operation (mantener conexión activa)."""
    if command.require_args(0):
        return 200, "Noop Ok"
    else:
        return 501, "Syntax error in parameters"