import logging
from comm.message import Message
from app.processing.command import Command
from app.router.FTPSession import FTPSession
from app.processing.processing_node import ProcessingNode

logger = logging.getLogger("dftp.processing.handlers.pasv")


def handle_pasv(
    command: Command,
    client_session: FTPSession,
    processing_node: ProcessingNode
):
    """
    Maneja comando PASV (modo pasivo).

    Flujo:
    - Validar sesión
    - Solicitar al DataNode apertura PASV
    - Guardar estado en la sesión
    - Responder 227
    """

    # ---------- Validaciones ----------
    if not client_session.authenticated:
        return 530, "Not logged in"

    # RFC: PASV no acepta argumentos, pero no es error fatal
    if command.arg_count() != 0:
        return 501, "Syntax error in parameters"

    # Limpiar PASV previo si existía
    client_session.cleanup_pasv()

    # ---------- Seleccionar DataNode ----------
    data_node_ip, data_node_port = processing_node.get_data_node()
    if not data_node_ip:
        return 425, "Can't open data connection"

    # ---------- Solicitar apertura PASV ----------
    msg = Message(
        type="OPEN_PASV",
        src=processing_node.ip,
        dst=data_node_ip,
        payload={
            "session_id": client_session.session_id,
            "client_ip": getattr(client_session, "client_ip", None)
        }
    )

    try:
        response = processing_node.send_message(
            data_node_ip,
            data_node_port,
            msg,
            await_response=True,
            timeout=2.0
        )
    except Exception:
        logger.exception("Error contacting DataNode for PASV")
        return 425, "Can't open data connection"

    if not response or response.payload.get("status") != "OK":
        return 425, "Can't open data connection"

    # ---------- Extraer datos ----------
    pasv_ip = response.payload.get("ip")
    pasv_port = response.payload.get("port")

    if not pasv_ip or not pasv_port:
        return 425, "Can't open data connection"

    # ---------- Guardar estado PASV ----------
    client_session.set_pasv(
        data_node_ip=data_node_ip,
        data_port=pasv_port
    )

    # ---------- Construir respuesta FTP ----------
    ip_parts = pasv_ip.split(".")
    port_high = pasv_port // 256
    port_low = pasv_port % 256

    return (
        227,
        f"Entering Passive Mode ({','.join(ip_parts)},{port_high},{port_low})"
    )
