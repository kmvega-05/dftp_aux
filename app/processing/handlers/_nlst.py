# from comm.message import Message
# from app.processing.command import Command
# from app.router.FTPSession import FTPSession
# from app.processing.processing_node import ProcessingNode


# def handle_nlist(
#     command: Command,
#     client_session: FTPSession,
#     processing_node: ProcessingNode
# ):
#     if not client_session.authenticated:
#         return 530, "Not logged in"

#     if command.arg_count() > 1:
#         return 501, "Syntax error in parameters"

#     if not client_session.pasv_mode:
#         return 425, "Use PASV first"

#     data_node_ip, data_node_port = processing_node.get_data_node()

#     list_path = command.get_arg(0) if command.arg_count() == 1 else "."

#     # 1️⃣ ordenar transferencia
#     msg = Message(
#         type="DATA_LIST",
#         src=processing_node.ip,
#         dst=data_node_ip,
#         payload={
#             "session_id": client_session.session_id,
#             "root": client_session.root_directory,
#             "cwd": client_session.current_path,
#             "path": list_path
#         }
#     )

#     try:
#         response = processing_node.send_message(
#             data_node_ip,
#             data_node_port,
#             msg,
#             await_response=True,
#             timeout=5.0
#         )
#     except Exception:
#         return 425, "Can't open data connection"

#     if not response or response.payload.get("status") != "OK":
#         return 550, response.payload.get("msg", "LIST failed")

#     # 2️⃣ FTP correcto: 226 al final
#     client_session.cleanup_pasv()
#     return 226, "Directory send OK"
