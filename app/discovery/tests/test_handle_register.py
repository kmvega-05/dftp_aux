import unittest
import os
from app.discovery import DiscoveryNode, ServiceRegister, NodeType
from comm import Message

class TestDiscoveryNodeRegisterWithOnMessage(unittest.TestCase):

    def setUp(self):
        # Definir la variable de entorno para subnet
        os.environ["DISCOVERY_SUBNET"] = "192.168.1.0/24"

        # Crear un DiscoveryNode en modo testing
        self.node = DiscoveryNode(
            node_name="discovery1",
            ip="127.0.0.1",
            port=9100,
            testing=True
        )
        print("[Setup] DiscoveryNode creado para testing")

    def test_register_valid_node(self):
        msg = Message(
            type="DISCOVERY_REGISTER",
            src="192.168.1.10",
            dst=self.node.ip,
            payload={
                "name": "node1",
                "ip": "192.168.1.10",
                "type": "ROUTING"
            }
        )
        response = self.node._on_message(msg, None)

        # Register no devuelve respuesta
        self.assertIsNone(response)

        node = self.node.register_table.get_node("node1")
        self.assertIsNotNone(node)
        self.assertEqual(node.name, "node1")
        self.assertEqual(node.ip, "192.168.1.10")
        self.assertEqual(node.node_type, NodeType.ROUTING)

        print("[Test] test_register_valid_node completado correctamente")

    def test_register_missing_fields(self):
        msg = Message(
            type="DISCOVERY_REGISTER",
            src="192.168.1.11",
            dst=self.node.ip,
            payload={"name": "node2"}  # falta ip y type
        )
        response = self.node._on_message(msg, None)
        self.assertIsNone(response)

        node = self.node.register_table.get_node("node2")
        self.assertIsNone(node)

        print("[Test] test_register_missing_fields completado correctamente")

    def test_register_invalid_type(self):
        msg = Message(
            type="DISCOVERY_REGISTER",
            src="192.168.1.12",
            dst=self.node.ip,
            payload={
                "name": "node3",
                "ip": "192.168.1.12",
                "type": "INVALID_TYPE"
            }
        )
        response = self.node._on_message(msg, None)
        self.assertIsNone(response)

        node = self.node.register_table.get_node("node3")
        self.assertIsNone(node)

        print("[Test] test_register_invalid_type completado correctamente")

if __name__ == "__main__":
    print("[Main] Iniciando tests de DiscoveryNode register...")
    unittest.main()
    print("[Main] Todos los tests completados")

