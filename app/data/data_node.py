import ipaddress
import logging
import os
from random import random
import socket
from app.data.file_manager import FileSystemManager
from app.node_type import NodeType
from comm.message import Message
from location.location_node import LocationNode

logger = logging.getLogger(__name__)

class DataNode(LocationNode):
    def __init__(self, node_name, ip, port, discovery_port = 9100, discovery_timeout = 0.8, heartbeat_interval = 2, node_type = None, discovery_workers = 32):
        super().__init__(node_name, ip, port, discovery_port, discovery_timeout, heartbeat_interval, node_type, discovery_workers)
        self.node_type = NodeType.DATA
        self.file_system_manager: FileSystemManager = FileSystemManager()
        self.pasv_sockets: dict[str, socket.socket] = {}  # La key es el session_id 

        self.register_handler('CHECK_EXISTS', self.check_exists_handler())
        self.register_handler('CHECK_DELE', self.check_dele_handler())
        self.register_handler('CHECK_MKD', self.check_mkd_handler())
        self.register_handler('CHECK_RMD', self.check_rmd_handler())
        self.register_handler('CHECK_RNTO', self.check_rnto_handler())
        self.register_handler('OPEN_PASV', self.open_pasv_handler())
        self.register_handler('DATA_LIST', self.data_list_handler())


    def check_exists_handler(self, message: 'Message', sock):
        payload = message.payload
        root = payload['root']
        current = payload['current']
        path = payload['path']
        want = payload['want']
        virtual, _ = self.file_system_manager.exists(root, current, path, want)
        return Message(
            type='CHECK_EXISTS_RESPONSE',
            src= self.ip,
            dst= message.header.get('src'),
            payload={
                "path": virtual
            }
        )
    
    def check_dele_handler(self, message: 'Message', sock):
        payload = message.payload
        root = payload['root']
        current = payload['current']
        path = payload['path']
        result, msg = self.file_system_manager.delete_file(root, current, path)
        return Message(
            type='CHECK_DELE_RESPONSE',
            src=self.ip,
            dst=message.header.get('src'),
            payload={
                'action': result,
                'msg': msg
            }
        )
    
    def check_mkd_handler(self, message: 'Message', sock):
        payload = message.payload
        root = payload['root']
        current = payload['current']
        dir = payload['dir']
        result, msg = self.file_system_manager.make_dir(root, current, dir)
        return Message(
            type='CHECK_MKD_RESPONSE',
            src=self.ip,
            dst=message.header.get('src'),
            payload={
                'action': result,
                'msg': msg
            }
        )
    
    def check_rmd_handler(self, message: 'Message', sock):
        payload = message.payload
        root = payload['root']
        current = payload['current']
        dir = payload['dir']
        result, msg = self.file_system_manager.remove_dir(root, current, dir)
        return Message(
            type='CHECK_RMD_RESPONSE',
            src=self.ip,
            dst=message.header.get('src'),
            payload={
                'action': result,
                'msg': msg
            }
        )
    
    def check_rnto_handler(self, message: 'Message', sock):
        payload = message.payload
        root = payload['root']
        current = payload['current']
        old = payload['old']
        new = payload['new']
        result, msg = self.file_system_manager.rename(root, current, old, new)
        return Message(
            type='CHECK_RNTO_RESPONSE',
            src=self.ip,
            dst=message.header.get('src'),
            payload={
                'action': result,
                'msg': msg
            }
        )
    
    def open_pasv_handler(self, message: Message, sock):
        payload = message.payload
        session_id = payload["session_id"]
        client_ip = payload.get("client_ip")
        port_min = int(os.getenv("PASV_MIN_PORT", "30000"))
        port_max = int(os.getenv("PASV_MAX_PORT", "30100"))
        try:
            data_socket, data_port = self._create_data_socket(port_min, port_max)
            self.pasv_sockets[session_id] = data_socket
            pasv_ip = self._get_pasv_ip(client_ip)
            return Message(
                type="OPEN_PASV_RESPONSE",
                src=self.ip,
                dst=message.header["src"],
                payload={
                    "status": "OK",
                    "ip": pasv_ip,
                    "port": data_port
                }
            )
        except Exception as e:
            logger.exception("PASV error")
            return Message(
                type="OPEN_PASV_RESPONSE",
                src=self.ip,
                dst=message.header["src"],
                payload={
                    "status": "ERROR",
                    "msg": str(e)
                }
            )
        
    def data_list_handler(self, message: Message, sock):
        payload = message.payload
        session_id = payload["session_id"]
        root = payload["root"]
        cwd = payload["cwd"]
        path = payload["path"]

        data_socket = self.pasv_sockets.get(session_id)
        if not data_socket:
            return Message(
                type="DATA_LIST_RESPONSE",
                src=self.ip,
                dst=message.header["src"],
                payload={
                    "status": "ERROR",
                    "msg": "PASV not initialized"
                }
            )
        try:
            # 1️⃣ aceptar conexión
            data_conn, _ = data_socket.accept()
            
            # 2️⃣ obtener listado
            list_info = self.file_system_manager.list_dir_detailed(
                root, cwd, path
            )

            # 3️⃣ formatear salida FTP LIST
            lines = []
            for info in list_info:
                typ = "d" if info.get("is_dir") else "-"
                size = info.get("size", 0)
                mtime = info.get("modified", "")
                name = info.get("name")
                lines.append(f"{typ} {size:>8} {mtime} {name}")

            listing = "\r\n".join(lines) + "\r\n" if lines else ""

            # 4️⃣ enviar datos
            data_conn.sendall(listing.encode("utf-8"))
            data_conn.close()

            return Message(
                type="DATA_LIST_RESPONSE",
                src=self.ip,
                dst=message.header["src"],
                payload={
                    "status": "OK"
                }
            )

        except Exception as e:
            logger.exception("DATA_LIST error")
            return Message(
                type="DATA_LIST_RESPONSE",
                src=self.ip,
                dst=message.header["src"],
                payload={
                    "status": "ERROR",
                    "msg": str(e)
                }
            )

        finally:
            # 5️⃣ limpieza PASV
            try:
                data_socket.close()
            except Exception:
                pass
            self.pasv_sockets.pop(session_id, None)

    def _create_data_socket(self, port_min, port_max):
        for _ in range(50):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            port = random.randint(port_min, port_max)
            try:
                sock.bind(("0.0.0.0", port))
                sock.listen(1)
                return sock, port
            except OSError:
                sock.close()
        raise RuntimeError("No free PASV port")

    def _get_pasv_ip(self, client_ip):
        overlay_range = os.getenv("OVERLAY_SUBNET", "10.0.0.0/8")
        advertise = os.getenv("PASV_ADVERTISE_HOST")

        if not client_ip:
            return advertise or socket.gethostbyname(socket.gethostname())

        try:
            client = ipaddress.ip_address(client_ip)
            overlay = ipaddress.ip_network(overlay_range, strict=False)
            if client in overlay:
                return socket.gethostbyname(socket.gethostname())
        except Exception:
            pass

        return advertise or socket.gethostbyname(socket.gethostname())

