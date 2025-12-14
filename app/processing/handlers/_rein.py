from app.processing.command import Command
from app.router.FTPSession import FTPSession


def handle_rein(command: 'Command', client_session: 'FTPSession', processing_node):
    """Maneja comando REIN - reinicializa la sesión FTP."""
    if command.require_args(0):
        return 220, "Service ready for new user"
    else:
        return 501, "Syntax error in parameters"