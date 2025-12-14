import json
import os
import bcrypt

from comm.message import Message
from location.location_node import LocationNode
from app.node_type import NodeType

class AuthNode(LocationNode):
    def __init__(self, node_name, ip, port, discovery_port = 9100, discovery_timeout = 0.8, heartbeat_interval = 2, node_type = None, discovery_workers = 32):
        super().__init__(node_name, ip, port, discovery_port, discovery_timeout, heartbeat_interval, node_type, discovery_workers)
        self.node_type = NodeType.AUTH
        self.register_handler('CHECK_USER', self.check_user_handler)
        self.register_handler('CHECK_PASS', self.check_pass_handler)
        
    def check_user_handler(self, message: 'Message', sock):
        payload = message.payload
        username = payload.get("username", "")
        result = self.user_exists(username)
        return Message(
            type="CHECK_USER_RESPONSE",
            src= self.ip,
            dst=message.header.get("src"),
            payload= {
                "result": result
            }
        )
    
    def check_pass_handler(self, message: 'Message', sock):
        payload = message.payload
        result = self.validate_password(payload["username"], payload['password'])
        return Message(
            type="CHECK_PASS_RESPONSE",
            src= self.ip,
            dst=message.header.get("src"),
            payload= {
                "result": result
            }
        )

    def get_users_file_path(self):
        """Obtiene la ruta al archivo de usuarios"""
        return os.path.join(os.path.dirname(__file__), '..', 'data', 'users.json')

    def get_user_by_name(self, username):
        """Busca un usuario por nombre, retorna el usuario completo o None"""
        try:
            users_file = self.get_users_file_path()
            with open(users_file, 'r') as f:
                data = json.load(f)
            
            for user in data.get('users', []):
                if user['username'] == username:
                    return user
            return None
        except Exception as e:
            print(f"Error reading users file: {e}")
            return None

    def user_exists(self,username):
        """Verifica si un usuario existe"""
        return self.get_user_by_name(username) is not None

    def validate_password(self,username, password):
        """Valida la contraseña de un usuario"""
        user = self.get_user_by_name(username)
        if user and 'password' in user:
            # Verificar la contraseña encriptada
            return bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8'))
        return False