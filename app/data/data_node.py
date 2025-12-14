from app.data.file_manager import FileSystemManager
from app.node_type import NodeType
from comm.message import Message
from location.location_node import LocationNode


class DataNode(LocationNode):
    def __init__(self, node_name, ip, port, discovery_port = 9100, discovery_timeout = 0.8, heartbeat_interval = 2, node_type = None, discovery_workers = 32):
        super().__init__(node_name, ip, port, discovery_port, discovery_timeout, heartbeat_interval, node_type, discovery_workers)
        self.node_type = NodeType.DATA
        self.file_system_manager: FileSystemManager = FileSystemManager()

        self.register_handler('CHECK_EXISTS', self.check_exists_handler())

    def check_exists_handler(self, message: 'Message', sock):
        payload = message.payload
        root = payload['root']
        current = payload['current']
        absolute = payload['absolute']
        want = payload['want']
        virtual, _ = self.file_system_manager.exists(root, current, absolute, want)
        return Message(
            type='CHECK_EXISTS_RESPONSE',
            src= self.ip,
            dst= message.header.get('src'),
            payload={
                "path": virtual
            }
        )