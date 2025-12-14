from app.processing.command import Command
from app.router.FTPSession import FTPSession


def handle_quit(command: 'Command', client_session: 'FTPSession', processing_node):
    if not command.require_args(0):
        return 501, "Syntax error in parameters" 
    can_close_now = client_session.request_quit()
    if can_close_now:
        # Cerrar inmediatamente
        return 221, "Goodbye"
    else:
        # Indicar que la petición fue recibida y será atendida cuando termine la transferencia
        return 200, "QUIT pending: will close after transfers complete"