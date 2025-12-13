import unittest
import os
import time
from app.discovery import DiscoveryNode, ServiceRegister, NodeType
from comm import Message

class TestDiscoveryNodeHeartbeat(unittest.TestCase):

    def setUp(self):
        os.environ["DISCOVERY_SUBNET"] = "192.168.1.0/24"

        self.node = DiscoveryNode(
            node_name="discovery1",
            ip="127.0.0.1",
            port=9100,
            testing=True
        )
        print("[Setup] DiscoveryNode creado para testing")

    def test_heartbeat_updates_timestamp(self):
        # Registrar un nodo manualmente
        node = ServiceRegister("node1", "192.168.1.10", NodeType.ROUTING)
        self.node.register_table.add_node(node)
        old_timestamp = node.last_heartbeat
        print(f"[Before] last_heartbeat = {old_timestamp}")

        time.sleep(0.1)  # asegurar diferencia de tiempo

        # Crear mensaje de heartbeat
        msg = Message(
            type="DISCOVERY_HEARTBEAT",
            src="192.168.1.10",
            dst=self.node.ip,
            payload={"name": "node1"}
        )

        # Procesar mensaje usando _on_message
        response = self.node._on_message(msg, None)

        self.assertIsNone(response)

        # Verificar que last_heartbeat se actualizó
        updated_node = self.node.register_table.get_node("node1")
        new_timestamp = updated_node.last_heartbeat
        print(f"[After] last_heartbeat = {new_timestamp}")

        self.assertGreater(new_timestamp, old_timestamp)
        print("[Test] test_heartbeat_updates_timestamp completado correctamente")

    def test_heartbeat_unknown_node(self):
        msg = Message(
            type="DISCOVERY_HEARTBEAT",
            src="192.168.1.11",
            dst=self.node.ip,
            payload={"name": "unknown_node"}
        )

        response = self.node._on_message(msg, None)
        self.assertIsNone(response)
        print("[Test] test_heartbeat_unknown_node completado correctamente")

if __name__ == "__main__":
    print("[Main] Iniciando tests de DiscoveryNode heartbeat...")
    unittest.main()
    print("[Main] Todos los tests completados")
